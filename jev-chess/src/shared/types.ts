export type RunnerStatus = "idle" | "running" | "paused" | "finished" | "error";

export interface MoveRecord {
  color: "w" | "b";
  san: string;
  lan: string;
  from: string;
  to: string;
  piece: string;
  captured?: string;
  promotion?: string;
  flags: string;
}

export interface LastDecision {
  move: string;
  confidence?: number;
  optionsConsidered: number;
  optionsPresented: number;
  selectionRounds: number;
  probabilityDistribution: Array<{ move: string; probability: number }>;
}

export interface GameState {
  fen: string;
  pgn: string;
  turn: "w" | "b";
  moves: MoveRecord[];
  decisions: number;
  status: RunnerStatus;
  message: string;
  isCheck: boolean;
  moveDelayMs: number;
  lastDecision?: LastDecision;
  updatedAt: string;
}
