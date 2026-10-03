import type { Move } from "chess.js";
import type { PositionSummary } from "./decision-facts.js";

interface JevResponse {
  model?: string;
  answers?: {
    move?: {
      choice?: string;
      confidence?: number;
      probabilities?: Record<string, number>;
    };
  };
}

export interface CandidateMove {
  id: string;
  move: Move;
  description: string;
}

export interface ChoiceResult {
  candidate: CandidateMove;
  confidence?: number;
  probabilities: Record<string, number>;
}

export interface DecisionContext {
  fen: string;
  pgn: string;
  turn: "w" | "b";
  history: string[];
  isCheck: boolean;
  legalMoveCount: number;
  eligibleMoveCount: number;
  excludedMateInOneCount: number;
  mateInOneMoveCount: number;
  excludedRepetitionCount: number;
  repetitionDrawMoveCount: number;
  materialLead: number;
  selectionRound: number;
  selectionStage: "group" | "final";
  positionSummary: PositionSummary;
  candidates: CandidateMove[];
}

const endpointUrl = process.env.JEV_API_URL ?? "https://ai-gateway.vercel.sh/v1/evaluate";
const model = process.env.JEV_MODEL ?? "typesafe-ai/jev";
const apiKey = process.env.AI_GATEWAY_API_KEY || process.env.JEV_API_KEY || process.env.VERCEL_OIDC_TOKEN;
const timeoutMs = Number(process.env.JEV_REQUEST_TIMEOUT_MS ?? 30_000);

export async function chooseMove(context: DecisionContext): Promise<ChoiceResult> {
  const criteria = Object.fromEntries(
    context.candidates.map(({ id, description }) => [id, description]),
  );
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const startedAt = Date.now();

  const requestBody = {
    model,
    state: {
      game: "standard chess",
      fen: context.fen,
      pgn: context.pgn,
      side_to_move: context.turn === "w" ? "white" : "black",
      recent_moves: context.history.slice(-24),
      is_check: context.isCheck,
      position_summary: context.positionSummary,
      legal_move_count: context.legalMoveCount,
      eligible_move_count: context.eligibleMoveCount,
      excluded_mate_in_one_count: context.excludedMateInOneCount,
      mate_in_one_move_count: context.mateInOneMoveCount,
      excluded_repetition_count: context.excludedRepetitionCount,
      repetition_draw_move_count: context.repetitionDrawMoveCount,
      current_side_material_lead: context.materialLead,
      selection_round: context.selectionRound,
      selection_stage: context.selectionStage,
      mate_in_one_filter_applied: context.excludedMateInOneCount > 0,
      decision_guidance:
        "Use the board, material points, and candidate facts to weigh tactics and king safety. Attack-map facts can include pinned attackers; immediate capture notes are legal replies. Avoid allowing immediate checkmate when a safe candidate exists. When materially ahead, prefer a non-drawing move over an immediate threefold-repetition draw when available. Choose only from the supplied candidates.",
      selection_note: selectionNote(context),
    },
    questions: {
      move: {
        type: "choice",
        instructions:
          "Which legal chess move is best for the side to move? Consider king safety, tactics, material, and improving the position. Choose only from the supplied moves.",
        criteria,
      },
    },
  };

  try {
    const response = await fetch(endpointUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });
    const responseText = await response.text();
    if (!response.ok) {
      throw new Error(`Jev-compatible endpoint returned HTTP ${response.status}: ${responseText.slice(0, 1200)}`);
    }

    let payload: JevResponse;
    try {
      payload = JSON.parse(responseText) as JevResponse;
    } catch {
      throw new Error(`Jev-compatible endpoint returned invalid JSON: ${responseText.slice(0, 1200)}`);
    }
    const answer = payload.answers?.move;
    const candidate = context.candidates.find((option) => option.id === answer?.choice);
    if (!answer?.choice || !candidate) {
      throw new Error(`Jev selected unknown move ${JSON.stringify(answer?.choice)}`);
    }

    const outcome = {
      candidate,
      confidence: answer.confidence,
      probabilities: answer.probabilities ?? {},
    };
    await logCall({
      at: new Date().toISOString(),
      elapsedMs: Date.now() - startedAt,
      request: requestBody,
      response: payload,
    });
    return outcome;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await logCall({
      at: new Date().toISOString(),
      elapsedMs: Date.now() - startedAt,
      request: requestBody,
      error: message,
    });
    throw new Error(message, { cause: error });
  } finally {
    clearTimeout(timeout);
  }
}

function selectionNote(context: DecisionContext): string {
  const guidance: string[] = [];
  if (context.excludedMateInOneCount > 0) {
    guidance.push(`${context.excludedMateInOneCount} moves that allow immediate checkmate were excluded`);
  } else if (context.mateInOneMoveCount > 0) {
    guidance.push("every legal move allows immediate checkmate; choose the best practical resistance");
  }
  if (context.excludedRepetitionCount > 0) {
    guidance.push(`${context.excludedRepetitionCount} moves that immediately draw by threefold repetition were excluded because you are materially ahead`);
  } else if (context.repetitionDrawMoveCount > 0) {
    guidance.push(`${context.repetitionDrawMoveCount} listed moves immediately draw by threefold repetition`);
  }
  const safety = guidance.length ? ` ${guidance.join("; ")}.` : "";
  if (context.selectionStage === "group") {
    return `Choose the strongest move in this balanced group. Winners advance to the next round.${safety}`;
  }
  if (context.selectionRound > 1) {
    return `Choose the strongest move among these finalists from ${context.eligibleMoveCount} eligible moves.${safety}`;
  }
  if (
    context.excludedMateInOneCount > 0 ||
    context.mateInOneMoveCount > 0 ||
    context.excludedRepetitionCount > 0 ||
    context.repetitionDrawMoveCount > 0
  ) {
    return `Choose the strongest move among ${context.eligibleMoveCount} eligible moves.${safety}`;
  }
  return "Choose the strongest move for the position.";
}

async function logCall(record: Record<string, unknown>): Promise<void> {
  const { appendFile, mkdir } = await import("node:fs/promises");
  const { resolve } = await import("node:path");
  const logDir = resolve(process.cwd(), "logs");
  await mkdir(logDir, { recursive: true });
  await appendFile(resolve(logDir, "jev-calls.jsonl"), `${JSON.stringify(record)}\n`);
}
