import { useEffect, useMemo, useState } from "react";
import { Chessboard } from "react-chessboard";
import type { GameState } from "../shared/types.js";

const emptyState: GameState = {
  fen: "start",
  pgn: "",
  turn: "w",
  moves: [],
  decisions: 0,
  status: "idle",
  message: "Ready to start a new game.",
  isCheck: false,
  moveDelayMs: 900,
  updatedAt: new Date(0).toISOString(),
};

export function App() {
  const [game, setGame] = useState<GameState>(emptyState);
  const [error, setError] = useState("");
  const [speed, setSpeed] = useState(emptyState.moveDelayMs);

  useEffect(() => {
    let active = true;
    const update = async () => {
      try {
        const response = await fetch("/api/state", { cache: "no-store" });
        if (!response.ok) throw new Error(`Game server returned ${response.status}`);
        const next = (await response.json()) as GameState;
        if (active) {
          setGame(next);
          setSpeed(next.moveDelayMs);
          setError("");
        }
      } catch (fetchError) {
        if (active) setError(fetchError instanceof Error ? fetchError.message : String(fetchError));
      }
    };
    void update();
    const timer = window.setInterval(update, 500);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const movePairs = useMemo(() => {
    const pairs: Array<{ number: number; white?: string; black?: string }> = [];
    for (let index = 0; index < game.moves.length; index += 2) {
      pairs.push({
        number: Math.floor(index / 2) + 1,
        white: game.moves[index]?.san,
        black: game.moves[index + 1]?.san,
      });
    }
    return pairs;
  }, [game.moves]);

  async function command(path: string, body?: unknown) {
    setError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? `Request failed: ${response.status}`);
      setGame(result as GameState);
    } catch (commandError) {
      setError(commandError instanceof Error ? commandError.message : String(commandError));
    }
  }

  const statusClass = `status status-${game.status}`;
  const activeTurn = game.status === "running" ? (game.turn === "w" ? "White to move" : "Black to move") : game.status;

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Jev Chess home">
          <span className="brand-mark">♞</span>
          <span>JEV<span className="brand-light">CHESS</span></span>
        </a>
        <div className="topbar-meta">
          <span className="live-dot" />
          <span>DECISION ENGINE DEMO</span>
          <span className="topbar-divider" />
          <span>STANDARD · 2 PLAYERS</span>
        </div>
        <a className="repo-link" href="https://github.com/christianmat/jev-pokemon" target="_blank" rel="noreferrer">
          INSPIRED BY JEv PLAYS POKÉMON <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="intro-row" id="top">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> AUTONOMOUS CHESS EXPERIMENT</div>
          <h1>One board. <em>Two minds.</em></h1>
          <p className="intro-copy">Jev chooses every move. The chess rules stay deterministic.</p>
        </div>
        <div className="round-card">
          <span className="round-label">DECISIONS MADE</span>
          <strong>{String(game.decisions).padStart(3, "0")}</strong>
          <span className={statusClass}><i /> {activeTurn}</span>
        </div>
      </section>

      <section className="game-layout">
        <div className="board-column">
          <div className="player-bar player-top">
            <div className="avatar avatar-black">♚</div>
            <div className="player-info"><strong>Jev</strong><span>BLACK · DECISION MODEL</span></div>
            {game.turn === "b" && game.status === "running" && <span className="thinking"><i /> THINKING</span>}
          </div>

          <div className="board-frame">
            <Chessboard options={{
              position: game.fen === "start" ? undefined : game.fen,
              boardOrientation: "white",
              allowDragging: false,
              showAnimations: true,
              animationDurationInMs: 250,
              showNotation: true,
              boardStyle: { borderRadius: "4px", overflow: "hidden" },
            }} />
            {game.isCheck && <div className="check-flag">CHECK</div>}
          </div>

          <div className="player-bar player-bottom">
            <div className="avatar avatar-white">♔</div>
            <div className="player-info"><strong>Jev</strong><span>WHITE · DECISION MODEL</span></div>
            {game.turn === "w" && game.status === "running" && <span className="thinking"><i /> THINKING</span>}
          </div>

          <div className="board-caption">
            <span><i className="square-swatch light" /> White</span>
            <span><i className="square-swatch dark" /> Black</span>
            <span className="rules-caption">LEGAL MOVES · {game.moves.length} PLY</span>
          </div>
        </div>

        <aside className="side-panel">
          <div className="last-decision">
            <span className="card-label">LAST DECISION</span>
            {game.lastDecision ? (
              <>
                <div className="decision-move">
                  <strong>{game.lastDecision.move}</strong>
                  <span>{game.lastDecision.optionsConsidered} legal moves considered</span>
                </div>
                <div className="distribution-heading">
                  <span>Jev’s move probabilities</span>
                  <span>{game.lastDecision.selectionRounds > 1
                    ? `Final choice · ${game.lastDecision.optionsPresented} finalists`
                    : `Among ${game.lastDecision.optionsPresented} options presented`}</span>
                </div>
                {game.lastDecision.probabilityDistribution.length ? (
                  <ol className="probability-list" aria-label="Jev move probability distribution">
                    {game.lastDecision.probabilityDistribution.map(({ move, probability }) => {
                      const percentage = probability * 100;
                      const selected = move === game.lastDecision?.move;
                      return (
                        <li className={`probability-row${selected ? " probability-selected" : ""}`} key={move}>
                          <span className="probability-move">{move}{selected && <small>CHOSEN</small>}</span>
                          <span className="probability-track" aria-hidden="true">
                            <span className="probability-fill" style={{ width: `${Math.min(100, percentage)}%` }} />
                          </span>
                          <span className="probability-value">{percentage.toFixed(1)}%</span>
                        </li>
                      );
                    })}
                  </ol>
                ) : (
                  <div className="probability-empty">The API did not return move probabilities for this decision.</div>
                )}
                <p className="probability-note">Choice probabilities show how Jev weighed the listed moves; they are not win chances.</p>
              </>
            ) : <div className="empty-decision">The first move is waiting for you.</div>}
          </div>

          <div className="panel-heading">
            <div><div className="eyebrow">LIVE MATCH</div><h2>Game control</h2></div>
            <span className="round-number">01</span>
          </div>

          <div className="game-status-card">
            <span className="card-label">GAME STATUS</span>
            <div className={statusClass}><i /> {game.status.toUpperCase()}</div>
            <p>{game.message}</p>
          </div>

          <div className="controls">
            {game.status === "running" ? (
              <button className="button button-primary" onClick={() => void command("/api/pause")}>
                <span>Ⅱ</span> Pause game
              </button>
            ) : (
              <button className="button button-primary" onClick={() => void command("/api/start")} disabled={game.status === "finished" || game.status === "error"}>
                <span>▶</span> {game.status === "paused" ? "Resume game" : "Start game"}
              </button>
            )}
            <button className="button button-secondary" onClick={() => void command("/api/reset")}>
              <span>↻</span> New game
            </button>
            <a className={`button button-tertiary ${game.moves.length ? "" : "disabled"}`} href={game.moves.length ? "/api/pgn" : undefined}>
              <span>↓</span> Download PGN
            </a>
          </div>

          <label className="speed-control">
            <span><span className="card-label">MOVE PACE</span><b>{speed < 500 ? "Quick" : speed > 1400 ? "Relaxed" : "Steady"}</b></span>
            <input type="range" min="250" max="2200" step="50" value={speed} onChange={(event) => {
              const moveDelayMs = Number(event.target.value);
              setSpeed(moveDelayMs);
              void command("/api/speed", { moveDelayMs });
            }} />
            <span className="speed-ends"><small>QUICK</small><small>RELAXED</small></span>
          </label>

          <div className="move-list">
            <div className="move-list-heading"><span className="card-label">MOVE HISTORY</span><span>{game.moves.length} moves</span></div>
            {movePairs.length ? (
              <div className="move-rows">
                {movePairs.map((pair) => (
                  <div className="move-row" key={pair.number}>
                    <span className="move-number">{String(pair.number).padStart(2, "0")}</span>
                    <span>{pair.white ?? "—"}</span>
                    <span>{pair.black ?? ""}</span>
                  </div>
                ))}
              </div>
            ) : <div className="empty-moves">Moves will appear here as the game unfolds.</div>}
          </div>

          {error && <div className="error-banner" role="alert">{error}</div>}

          <div className="system-note"><span>↳</span><p>The harness enforces legal moves, detects game endings, and keeps a decision log. Jev only selects from the moves it is given.</p></div>
        </aside>
      </section>

      <footer className="footer">
        <span>JEV CHESS <b>·</b> SYSTEM ONE DECISION STUDY</span>
        <span>OPEN SOURCE RULES &amp; BOARD</span>
      </footer>
    </main>
  );
}
