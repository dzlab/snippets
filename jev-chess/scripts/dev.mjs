import { spawn } from "node:child_process";

const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const children = [
  spawn(npm, ["run", "dev:server"], { stdio: "inherit" }),
  spawn(npm, ["run", "dev:web"], { stdio: "inherit" }),
];

function stop(signal = "SIGTERM") {
  for (const child of children) {
    if (!child.killed) child.kill(signal);
  }
}

process.on("SIGINT", () => stop("SIGINT"));
process.on("SIGTERM", () => stop("SIGTERM"));

for (const child of children) {
  child.on("exit", (code) => {
    if (code && code !== 0) process.exitCode = code;
    stop();
  });
}
