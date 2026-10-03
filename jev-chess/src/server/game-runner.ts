import { Chess, type Move } from "chess.js";
import type { GameState, LastDecision, MoveRecord, RunnerStatus } from "../shared/types.js";
import { analyzeCandidate, summarizePosition, type PositionSummary } from "./decision-facts.js";
import { chooseMove, type CandidateMove, type ChoiceResult } from "./jev-client.js";

const maxOptions = Math.max(2, Number(process.env.JEV_MAX_OPTIONS ?? 48));
const maxPlies = Math.max(1, Number(process.env.JEV_MAX_PLIES ?? 200));
const materialLeadToAvoidRepetition = 3;

export class ChessRunner {
  private chess = new Chess();
  private status: RunnerStatus = "idle";
  private message = "Ready to start a new game.";
  private generation = 0;
  private decisions = 0;
  private moveDelayMs = Math.max(0, Number(process.env.JEV_MOVE_DELAY_MS ?? 900));
  private lastDecision: LastDecision | undefined;
  private updatedAt = new Date().toISOString();

  getState(): GameState {
    return {
      fen: this.chess.fen(),
      pgn: this.chess.pgn(),
      turn: this.chess.turn(),
      moves: this.chess.history({ verbose: true }).map(toMoveRecord),
      decisions: this.decisions,
      status: this.status,
      message: this.message,
      isCheck: this.chess.isCheck(),
      moveDelayMs: this.moveDelayMs,
      lastDecision: this.lastDecision,
      updatedAt: this.updatedAt,
    };
  }

  start(): void {
    if (this.status === "running") return;
    const generation = ++this.generation;
    this.status = "running";
    this.message = "Jev is choosing a move.";
    this.touch();
    void this.run(generation);
  }

  pause(): void {
    if (this.status !== "running") return;
    this.generation++;
    this.status = "paused";
    this.message = "Game paused.";
    this.touch();
  }

  reset(): void {
    this.generation++;
    this.chess = new Chess();
    this.status = "idle";
    this.message = "New game ready.";
    this.decisions = 0;
    this.lastDecision = undefined;
    this.touch();
  }

  setMoveDelay(milliseconds: number): void {
    this.moveDelayMs = Math.min(10_000, Math.max(0, Math.round(milliseconds)));
    this.touch();
  }

  private async run(generation: number): Promise<void> {
    try {
      while (generation === this.generation && this.status === "running") {
        if (this.chess.isGameOver()) {
          this.finish(gameOverMessage(this.chess));
          return;
        }
        if (this.chess.history().length >= maxPlies) {
          this.finish(`Stopped at the ${maxPlies}-ply safety limit.`);
          return;
        }

        const legalMoves = this.chess.moves({ verbose: true });
        if (legalMoves.length === 0) {
          this.finish(gameOverMessage(this.chess));
          return;
        }

        const positionSummary = summarizePosition(this.chess);
        const selection = await this.chooseFromLegalMoves(legalMoves, positionSummary);
        if (generation !== this.generation || this.status !== "running") return;

        const chosen = selection.result.candidate.move;
        this.chess.move({ from: chosen.from, to: chosen.to, promotion: chosen.promotion });
        this.decisions++;
        this.lastDecision = {
          move: chosen.san,
          confidence: selection.result.confidence,
          optionsConsidered: legalMoves.length,
          optionsPresented: selection.optionsPresented,
          selectionRounds: selection.rounds,
          probabilityDistribution: selection.probabilityDistribution,
        };
        this.message = `${this.chess.turn() === "w" ? "Black" : "White"} played ${chosen.san}.`;
        this.touch();

        if (this.chess.isGameOver()) {
          this.finish(gameOverMessage(this.chess));
          return;
        }
        await delay(this.moveDelayMs);
      }
    } catch (error) {
      if (generation !== this.generation) return;
      this.status = "error";
      this.message = error instanceof Error ? error.message : String(error);
      this.touch();
    }
  }

  private async chooseFromLegalMoves(legalMoves: Move[], positionSummary: PositionSummary): Promise<{
    result: ChoiceResult;
    rounds: number;
    optionsPresented: number;
    probabilityDistribution: LastDecision["probabilityDistribution"];
  }> {
    const analyzed = legalMoves.map((move, index) => {
      const analysis = analyzeCandidate(this.chess, move);
      return {
        allowsMateInOne: analysis.allowsMateInOne,
        causesThreefoldDraw: analysis.causesThreefoldDraw,
        candidate: {
          id: `move_${index.toString().padStart(3, "0")}`,
          move,
          description: analysis.description,
        } satisfies CandidateMove,
      };
    });
    const legalMoveCount = analyzed.length;
    const safeCandidates = analyzed.filter(({ allowsMateInOne }) => !allowsMateInOne);
    const mateInOneMoveCount = legalMoveCount - safeCandidates.length;
    const excludedMateInOneCount = safeCandidates.length ? legalMoveCount - safeCandidates.length : 0;
    const candidatesAfterMateSafety = safeCandidates.length ? safeCandidates : analyzed;
    const materialLead = this.chess.turn() === "w"
      ? positionSummary.whiteMaterialAdvantage
      : -positionSummary.whiteMaterialAdvantage;
    const hasMaterialLead = materialLead >= materialLeadToAvoidRepetition;
    const nonRepeatingCandidates = candidatesAfterMateSafety.filter(({ causesThreefoldDraw }) => !causesThreefoldDraw);
    const excludedRepetitionCount = hasMaterialLead && nonRepeatingCandidates.length
      ? candidatesAfterMateSafety.length - nonRepeatingCandidates.length
      : 0;
    const repetitionDrawMoveCount = candidatesAfterMateSafety.filter(({ causesThreefoldDraw }) => causesThreefoldDraw).length;
    let candidates = (excludedRepetitionCount ? nonRepeatingCandidates : candidatesAfterMateSafety)
      .map(({ candidate }) => candidate);
    const eligibleMoveCount = candidates.length;
    let selectionRound = 1;

    while (candidates.length > maxOptions) {
      const winners: CandidateMove[] = [];
      for (const group of balancedGroups(candidates, maxOptions)) {
        const result = await this.ask(
          group,
          legalMoveCount,
          eligibleMoveCount,
          excludedMateInOneCount,
          mateInOneMoveCount,
          excludedRepetitionCount,
          repetitionDrawMoveCount,
          materialLead,
          selectionRound,
          "group",
          positionSummary,
        );
        winners.push({ ...result.candidate, id: `round_${selectionRound}_${winners.length}` });
      }
      candidates = winners;
      selectionRound++;
    }

    const result = await this.ask(
      candidates,
      legalMoveCount,
      eligibleMoveCount,
      excludedMateInOneCount,
      mateInOneMoveCount,
      excludedRepetitionCount,
      repetitionDrawMoveCount,
      materialLead,
      selectionRound,
      "final",
      positionSummary,
    );
    const probabilityDistribution = Object.entries(result.probabilities)
      .flatMap(([id, probability]) => {
        const candidate = candidates.find((option) => option.id === id);
        return candidate && Number.isFinite(probability) && probability >= 0
          ? [{ move: candidate.move.san, probability }]
          : [];
      })
      .sort((left, right) => right.probability - left.probability);
    return { result, rounds: selectionRound, optionsPresented: candidates.length, probabilityDistribution };
  }

  private async ask(
    candidates: CandidateMove[],
    legalMoveCount: number,
    eligibleMoveCount: number,
    excludedMateInOneCount: number,
    mateInOneMoveCount: number,
    excludedRepetitionCount: number,
    repetitionDrawMoveCount: number,
    materialLead: number,
    selectionRound: number,
    selectionStage: "group" | "final",
    positionSummary: PositionSummary,
  ): Promise<ChoiceResult> {
    return chooseMove({
      fen: this.chess.fen(),
      pgn: this.chess.pgn(),
      turn: this.chess.turn(),
      history: this.chess.history(),
      isCheck: this.chess.isCheck(),
      legalMoveCount,
      eligibleMoveCount,
      excludedMateInOneCount,
      mateInOneMoveCount,
      excludedRepetitionCount,
      repetitionDrawMoveCount,
      materialLead,
      selectionRound,
      selectionStage,
      positionSummary,
      candidates,
    });
  }

  private finish(message: string): void {
    this.generation++;
    this.status = "finished";
    this.message = message;
    this.touch();
  }

  private touch(): void {
    this.updatedAt = new Date().toISOString();
  }
}

function balancedGroups<T>(items: T[], maximumSize: number): T[][] {
  const groupCount = Math.ceil(items.length / maximumSize);
  const groups = Array.from({ length: groupCount }, () => [] as T[]);
  items.forEach((item, index) => groups[index % groupCount].push(item));
  return groups;
}

function toMoveRecord(move: Move): MoveRecord {
  return {
    color: move.color,
    san: move.san,
    lan: move.lan,
    from: move.from,
    to: move.to,
    piece: move.piece,
    captured: move.captured,
    promotion: move.promotion,
    flags: move.flags,
  };
}

function gameOverMessage(chess: Chess): string {
  if (chess.isCheckmate()) {
    const winner = chess.turn() === "w" ? "Black" : "White";
    return `Checkmate. ${winner} wins.`;
  }
  if (chess.isStalemate()) return "Draw by stalemate.";
  if (chess.isThreefoldRepetition()) return "Draw by threefold repetition.";
  if (chess.isInsufficientMaterial()) return "Draw by insufficient material.";
  if (chess.isDrawByFiftyMoves()) return "Draw by the fifty-move rule.";
  return "Game over.";
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
