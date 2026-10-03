import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { ChessRunner } from "./game-runner.js";

const port = Number(process.env.JEV_CHESS_PORT ?? 8788);
const root = process.cwd();
const clientDist = resolve(root, "dist");
const runner = new ChessRunner();

const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);
  try {
    if (url.pathname === "/api/state" && request.method === "GET") {
      return json(response, 200, runner.getState());
    }
    if (url.pathname === "/api/start" && request.method === "POST") {
      runner.start();
      return json(response, 202, runner.getState());
    }
    if (url.pathname === "/api/pause" && request.method === "POST") {
      runner.pause();
      return json(response, 200, runner.getState());
    }
    if (url.pathname === "/api/reset" && request.method === "POST") {
      runner.reset();
      return json(response, 200, runner.getState());
    }
    if (url.pathname === "/api/speed" && request.method === "POST") {
      const body = await readJson(request);
      if (typeof body.moveDelayMs !== "number" || !Number.isFinite(body.moveDelayMs)) {
        return json(response, 400, { error: "moveDelayMs must be a finite number" });
      }
      runner.setMoveDelay(body.moveDelayMs);
      return json(response, 200, runner.getState());
    }
    if (url.pathname === "/api/pgn" && request.method === "GET") {
      response.writeHead(200, {
        "content-type": "application/x-chess-pgn; charset=utf-8",
        "content-disposition": 'attachment; filename="jev-chess.pgn"',
      });
      return response.end(runner.getState().pgn || "[Result *]\n");
    }
    if (url.pathname.startsWith("/api/")) {
      return json(response, 404, { error: "Not found" });
    }
    return serveClient(request, response, url.pathname);
  } catch (error) {
    return json(response, 500, {
      error: error instanceof Error ? error.message : String(error),
    });
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Jev Chess server listening at http://127.0.0.1:${port}`);
});

async function serveClient(
  request: IncomingMessage,
  response: ServerResponse,
  pathname: string,
): Promise<void> {
  const target = resolve(clientDist, `.${decodeURIComponent(pathname)}`);
  if (target !== clientDist && !target.startsWith(clientDist + sep)) {
    return json(response, 403, { error: "Forbidden" });
  }
  let file = target;
  try {
    if ((await stat(file)).isDirectory()) file = resolve(file, "index.html");
  } catch {
    file = resolve(clientDist, "index.html");
  }
  const body = await readFile(file);
  response.writeHead(200, { "content-type": contentType(file), "cache-control": "no-store" });
  response.end(request.method === "HEAD" ? undefined : body);
}

function json(response: ServerResponse, status: number, body: unknown): void {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(JSON.stringify(body));
}

function contentType(file: string): string {
  switch (extname(file)) {
    case ".html": return "text/html; charset=utf-8";
    case ".js": return "text/javascript; charset=utf-8";
    case ".css": return "text/css; charset=utf-8";
    case ".svg": return "image/svg+xml";
    case ".png": return "image/png";
    case ".json": return "application/json; charset=utf-8";
    default: return "application/octet-stream";
  }
}

async function readJson(request: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of request) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    size += buffer.length;
    if (size > 16_384) throw new Error("Request body is too large");
    chunks.push(buffer);
  }
  const parsed: unknown = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Expected a JSON object");
  }
  return parsed as Record<string, unknown>;
}
