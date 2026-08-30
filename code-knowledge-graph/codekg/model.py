from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    path: str
    name: str
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "name": self.name,
            "text": self.text,
        }


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    kind: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "src": self.src,
            "dst": self.dst,
            "kind": self.kind,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class ParsedGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class Task:
    query: str
    gold_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "gold_files": list(self.gold_files),
        }


@dataclass(frozen=True)
class RankResult:
    items: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": list(self.items),
            "scores": list(self.scores),
        }
