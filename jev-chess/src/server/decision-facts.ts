import { Chess, type Color, type Move, type PieceSymbol, type Square } from "chess.js";

export interface PositionSummary {
  board: string;
  pieceCounts: Record<"white" | "black", Record<PieceSymbol, number>>;
  materialPoints: Record<"white" | "black", number>;
  whiteMaterialAdvantage: number;
  attackedPieces: Array<{
    color: "white" | "black";
    piece: PieceSymbol;
    square: Square;
    attackerCount: number;
    defenderCount: number;
  }>;
}

const files = "abcdefgh";
const materialValue: Record<PieceSymbol, number> = {
  p: 1,
  n: 3,
  b: 3,
  r: 5,
  q: 9,
  k: 0,
};

function emptyCounts(): Record<PieceSymbol, number> {
  return { p: 0, n: 0, b: 0, r: 0, q: 0, k: 0 };
}

function otherColor(color: Color): Color {
  return color === "w" ? "b" : "w";
}

function colorName(color: Color): "white" | "black" {
  return color === "w" ? "white" : "black";
}

function pieceName(piece: PieceSymbol): string {
  return {
    p: "pawn",
    n: "knight",
    b: "bishop",
    r: "rook",
    q: "queen",
    k: "king",
  }[piece];
}

function pieceLetter(type: PieceSymbol, color: Color): string {
  return color === "w" ? type.toUpperCase() : type;
}

export function summarizePosition(chess: Chess): PositionSummary {
  const pieceCounts = { white: emptyCounts(), black: emptyCounts() };
  const materialPoints = { white: 0, black: 0 };
  const attackedPieces: PositionSummary["attackedPieces"] = [];
  const ranks = chess.board();
  const board = [
    `  ${files.split("").join(" ")}`,
    ...ranks.map((rank, index) => {
      for (const cell of rank) {
        if (cell) {
          const color = colorName(cell.color);
          pieceCounts[color][cell.type]++;
          materialPoints[color] += materialValue[cell.type];
        }
      }
      const squares = rank.map((cell) => cell ? pieceLetter(cell.type, cell.color) : ".");
      return `${8 - index} ${squares.join(" ")}`;
    }),
    `  ${files.split("").join(" ")}`,
  ].join("\n");

  for (const rank of ranks) {
    for (const cell of rank) {
      if (!cell) continue;
      const attackers = chess.attackers(cell.square, otherColor(cell.color));
      if (attackers.length === 0) continue;
      attackedPieces.push({
        color: colorName(cell.color),
        piece: cell.type,
        square: cell.square,
        attackerCount: attackers.length,
        defenderCount: chess.attackers(cell.square, cell.color).length,
      });
    }
  }

  return {
    board,
    pieceCounts,
    materialPoints,
    whiteMaterialAdvantage: materialPoints.white - materialPoints.black,
    attackedPieces,
  };
}

function priorSquareForPiece(move: Move, square: Square, piece: PieceSymbol): Square | undefined {
  if (square === move.to) return move.from;
  const rank = move.color === "w" ? "1" : "8";
  if (piece === "r" && move.isKingsideCastle() && square === `f${rank}`) {
    return `h${rank}` as Square;
  }
  if (piece === "r" && move.isQueensideCastle() && square === `d${rank}`) {
    return `a${rank}` as Square;
  }
  return square;
}

function describeAttackChanges(before: Chess, after: Chess, move: Move): string[] {
  const changes: string[] = [];
  for (const rank of after.board()) {
    for (const piece of rank) {
      if (!piece) continue;
      const beforeSquare = piece.color === move.color
        ? priorSquareForPiece(move, piece.square, piece.type)
        : piece.square;
      if (!beforeSquare) continue;
      const priorPiece = before.get(beforeSquare);
      if (!priorPiece || priorPiece.color !== piece.color || priorPiece.type !== piece.type) continue;

      const attackedBy = otherColor(piece.color);
      const wasAttacked = before.isAttacked(beforeSquare, attackedBy);
      const isAttacked = after.isAttacked(piece.square, attackedBy);
      if (!wasAttacked && isAttacked) {
        changes.push(`${colorName(piece.color)} ${pieceName(piece.type)} on ${piece.square} is newly attacked by ${colorName(attackedBy)}`);
      } else if (wasAttacked && !isAttacked) {
        changes.push(`${colorName(piece.color)} ${pieceName(piece.type)} on ${piece.square} is no longer attacked by ${colorName(attackedBy)}`);
      }
    }
  }
  return changes;
}

function capturedSquare(move: Move): Square {
  if (!move.isEnPassant()) return move.to;
  const rank = Number(move.to[1]) + (move.color === "w" ? -1 : 1);
  return `${move.to[0]}${rank}` as Square;
}

function hasLegalRecapture(position: Chess, capture: Move): boolean {
  const afterCapture = new Chess(position.fen());
  afterCapture.move({ from: capture.from, to: capture.to, promotion: capture.promotion });
  return afterCapture.moves({ verbose: true }).some(
    (reply) => reply.captured && reply.to === capture.to,
  );
}

export interface CandidateAnalysis {
  description: string;
  allowsMateInOne: boolean;
  causesThreefoldDraw: boolean;
}

function cloneGame(chess: Chess): Chess {
  const clone = new Chess();
  const pgn = chess.pgn();
  if (pgn) clone.loadPgn(pgn);
  return clone;
}

export function analyzeCandidate(chess: Chess, move: Move): CandidateAnalysis {
  const details = [
    `${move.san} (${move.from} to ${move.to})`,
    `${pieceName(move.piece)}${move.captured ? ` captures ${pieceName(move.captured)} (+${materialValue[move.captured]} material points)` : ""}`,
    move.promotion ? `promotes to ${pieceName(move.promotion)}` : "",
  ].filter(Boolean);

  const afterMove = cloneGame(chess);
  afterMove.move({ from: move.from, to: move.to, promotion: move.promotion });
  details.push(...describeAttackChanges(chess, afterMove, move));

  if (afterMove.isCheckmate()) {
    details.push("checkmate");
    return { description: details.join("; "), allowsMateInOne: false, causesThreefoldDraw: false };
  }
  const causesThreefoldDraw = afterMove.isThreefoldRepetition();
  if (causesThreefoldDraw) details.push("draws immediately by threefold repetition");
  if (afterMove.isCheck()) details.push("gives check");

  const captures = afterMove.moves({ verbose: true }).filter((reply) => reply.captured);
  if (captures.length) {
    const targets = new Set(
      captures.map((reply) => `${pieceName(reply.captured!)} on ${capturedSquare(reply)}`),
    );
    details.push(`opponent has immediate legal captures of ${[...targets].join(", ")}`);
  }

  const movedPieceCaptures = captures.filter((reply) => capturedSquare(reply) === move.to);
  if (movedPieceCaptures.length) {
    const recaptureStatuses = movedPieceCaptures.map((capture) => hasLegalRecapture(afterMove, capture));
    if (recaptureStatuses.every(Boolean)) {
      details.push(`the moved ${pieceName(move.piece)} (${materialValue[move.piece]} material points) can be captured immediately, with a legal recapture available`);
    } else if (recaptureStatuses.some(Boolean)) {
      details.push(`the moved ${pieceName(move.piece)} (${materialValue[move.piece]} material points) can be captured immediately; at least one such capture allows a legal recapture`);
    } else {
      details.push(`the moved ${pieceName(move.piece)} (${materialValue[move.piece]} material points) can be captured immediately, with no legal recapture available`);
    }
  }

  const mateReplies: string[] = [];
  for (const reply of afterMove.moves({ verbose: true })) {
    const afterReply = new Chess(afterMove.fen());
    afterReply.move({ from: reply.from, to: reply.to, promotion: reply.promotion });
    if (afterReply.isCheckmate()) mateReplies.push(reply.san);
  }
  if (mateReplies.length) details.push(`allows immediate checkmate with ${mateReplies.join(", ")}`);

  return {
    description: details.join("; "),
    allowsMateInOne: mateReplies.length > 0,
    causesThreefoldDraw,
  };
}
