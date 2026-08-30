from __future__ import annotations

import subprocess
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Iterable

from .model import Edge
from .parser import scan_repository


def co_edit_edges(
    repo_root: str | Path,
    max_commits: int,
    max_files_per_commit: int,
    known_paths: Iterable[str] | None = None,
) -> list[Edge]:
    repo_path = Path(repo_root)
    command = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"--max-count={max_commits}",
        "--format=%x1e",
        "--name-only",
        "--diff-filter=ACMR",
        "-z",
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return []

    if known_paths is None:
        graph = scan_repository(repo_path)
        known_paths = {
            node.path
            for node in graph.nodes
            if node.kind == "file"
        }

    normalized_paths = {_normalize_path(path) for path in known_paths}
    pair_counts: Counter[tuple[str, str]] = Counter()
    blocks = result.stdout.split(b"\x1e")

    for block in blocks:
        all_commit_paths = sorted(
            {
                _normalize_path(entry.decode("utf-8").strip())
                for entry in block.split(b"\x00")
                if entry.strip()
            }
        )
        if len(all_commit_paths) < 2 or len(all_commit_paths) > max_files_per_commit:
            continue
        commit_paths = all_commit_paths
        if normalized_paths:
            commit_paths = [path for path in all_commit_paths if path in normalized_paths]
        if len(commit_paths) < 2:
            continue

        for left, right in combinations(commit_paths, 2):
            pair_counts[(left, right)] += 1

    return [
        Edge(src=f"file:{left}", dst=f"file:{right}", kind="co_edit", weight=float(weight))
        for (left, right), weight in sorted(pair_counts.items())
    ]


def _normalize_path(path: str) -> str:
    return Path(path).as_posix()
