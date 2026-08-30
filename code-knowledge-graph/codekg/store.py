from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .model import Node, ParsedGraph

_PROJECTABLE_EDGE_KINDS = {
    "import": "import",
    "imports": "import",
    "call": "call",
    "calls": "call",
    "contains": "contains",
    "co_edit": "co_edit",
}
_EDGE_KIND_ORDER = {
    "call": 0,
    "import": 1,
    "contains": 2,
    "co_edit": 3,
}


@dataclass(frozen=True)
class FileGraph:
    nodes: list[Node]
    adjacency: dict[str, list[str]]
    edge_labels: dict[tuple[str, str], tuple[str, ...]]
    weights: dict[tuple[str, str], float]


def open_store(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(Path(db_path)))
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            path TEXT,
            name TEXT,
            text TEXT
        );
        CREATE TABLE IF NOT EXISTS edges (
            src TEXT NOT NULL,
            dst TEXT NOT NULL,
            kind TEXT NOT NULL,
            weight REAL NOT NULL,
            PRIMARY KEY (src, dst, kind)
        );
        CREATE INDEX IF NOT EXISTS idx_edges_src ON edges (src);
        CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges (dst);
        CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes (path);
        """
    )
    return connection


def replace_graph(connection: sqlite3.Connection, graph: ParsedGraph) -> None:
    node_rows = [
        (node.id, node.kind, node.path, node.name, node.text)
        for node in graph.nodes
    ]
    edge_rows = [
        (
            edge.src,
            edge.dst,
            edge.kind,
            _validated_edge_weight(edge.weight, f"{edge.src}->{edge.dst}:{edge.kind}"),
        )
        for edge in graph.edges
    ]

    with connection:
        connection.execute("DELETE FROM edges")
        connection.execute("DELETE FROM nodes")
        connection.executemany(
            "INSERT INTO nodes (id, kind, path, name, text) VALUES (?, ?, ?, ?, ?)",
            node_rows,
        )
        connection.executemany(
            "INSERT INTO edges (src, dst, kind, weight) VALUES (?, ?, ?, ?)",
            edge_rows,
        )


def counts(connection: sqlite3.Connection) -> dict[str, int]:
    row = connection.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM nodes) AS node_count,
            (SELECT COUNT(*) FROM edges) AS edge_count
        """
    ).fetchone()
    return {
        "nodes": int(row["node_count"]),
        "edges": int(row["edge_count"]),
    }


def load_file_graph(connection: sqlite3.Connection) -> FileGraph:
    stored_nodes = [
        Node(
            id=row["id"],
            kind=row["kind"],
            path=row["path"] or "",
            name=row["name"] or "",
            text=row["text"] or "",
        )
        for row in connection.execute(
            "SELECT id, kind, path, name, text FROM nodes ORDER BY path, kind, name, id"
        )
    ]
    nodes_by_id = {node.id: node for node in stored_nodes}
    file_nodes = sorted(
        (
            node
            for node in stored_nodes
            if node.kind == "file" and node.path
        ),
        key=lambda node: (node.path, node.name, node.id),
    )
    file_paths = {node.path for node in file_nodes}

    undirected_weights: dict[tuple[str, str], float] = defaultdict(float)
    undirected_labels: dict[tuple[str, str], set[str]] = defaultdict(set)

    for row in connection.execute(
        "SELECT src, dst, kind, weight FROM edges ORDER BY src, dst, kind"
    ):
        label = _PROJECTABLE_EDGE_KINDS.get(row["kind"])
        if label is None:
            continue

        src_node = nodes_by_id.get(row["src"])
        dst_node = nodes_by_id.get(row["dst"])
        if src_node is None or dst_node is None:
            continue

        src_path = _path_for_node(src_node)
        dst_path = _path_for_node(dst_node)
        if not src_path or not dst_path or src_path == dst_path:
            continue
        if src_path not in file_paths or dst_path not in file_paths:
            continue

        weight = _validated_edge_weight(
            row["weight"],
            f"{row['src']}->{row['dst']}:{row['kind']}",
        )
        pair = _canonical_pair(src_path, dst_path)
        undirected_weights[pair] += weight
        undirected_labels[pair].add(label)

    adjacency = {path: [] for path in sorted(file_paths)}
    edge_labels: dict[tuple[str, str], tuple[str, ...]] = {}
    weights: dict[tuple[str, str], float] = {}

    for left, right in sorted(undirected_weights):
        labels = tuple(sorted(undirected_labels[(left, right)], key=_edge_kind_sort_key))
        weight = undirected_weights[(left, right)]
        for src_path, dst_path in ((left, right), (right, left)):
            adjacency[src_path].append(dst_path)
            edge_labels[(src_path, dst_path)] = labels
            weights[(src_path, dst_path)] = weight

    for neighbors in adjacency.values():
        neighbors.sort()

    return FileGraph(
        nodes=file_nodes,
        adjacency=adjacency,
        edge_labels=edge_labels,
        weights=weights,
    )


def _path_for_node(node: Node) -> str:
    return node.path


def _canonical_pair(left: str, right: str) -> tuple[str, str]:
    if left <= right:
        return (left, right)
    return (right, left)


def _edge_kind_sort_key(kind: str) -> tuple[int, str]:
    return (_EDGE_KIND_ORDER.get(kind, len(_EDGE_KIND_ORDER)), kind)


def _validated_edge_weight(weight: float, context: str) -> float:
    numeric_weight = float(weight)
    if not math.isfinite(numeric_weight) or numeric_weight <= 0.0:
        raise ValueError(
            f"edge weight must be finite and positive for {context}: {weight!r}"
        )
    return numeric_weight
