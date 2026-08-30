from __future__ import annotations

import math
import re
from collections import defaultdict

from .model import RankResult
from .store import FileGraph

_TOKEN_BOUNDARY_RE = re.compile(r"[^A-Za-z0-9]+")
_EDGE_GROUP_NAMES = {
    "call": "calls",
    "import": "imports",
    "contains": "contains",
    "co_edit": "co_edit",
}
_EDGE_GROUP_ORDER = ("imports", "calls", "contains", "co_edit")
_CONNECTED_SELF_LOOP_WEIGHT = 0.5


def tokenize_identifier(value: str) -> list[str]:
    with_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    normalized = _TOKEN_BOUNDARY_RE.sub(" ", with_boundaries.replace("\\", "/"))
    return [token for token in normalized.lower().split() if token]


def lexical_rank(query: str, file_graph: FileGraph) -> RankResult:
    query_tokens = set(tokenize_identifier(query))
    ranked = sorted(
        (
            (_lexical_score(node, query_tokens), node.path)
            for node in file_graph.nodes
        ),
        key=lambda item: (-item[0], item[1]),
    )
    return RankResult(
        items=[path for _, path in ranked],
        scores=[float(score) for score, _ in ranked],
    )


def graph_rank(
    query: str,
    file_graph: FileGraph,
    *,
    n_anchors: int = 3,
    damping: float = 0.85,
    max_iterations: int = 50,
    tolerance: float = 1e-9,
) -> RankResult:
    _validate_positive_integer("n_anchors", n_anchors)
    _validate_damping(damping)
    _validate_positive_integer("max_iterations", max_iterations)
    _validate_non_negative_number("tolerance", tolerance)

    if not file_graph.nodes:
        return RankResult()

    lexical = lexical_rank(query, file_graph)
    anchors = _top_anchors(lexical, n_anchors)
    paths = [node.path for node in file_graph.nodes]
    personalization = _personalization(paths, anchors)
    transitions = _build_transitions(paths, file_graph)
    scores = personalization.copy()

    for _ in range(max_iterations):
        dangling_mass = sum(scores[path] for path in paths if not transitions[path])
        next_scores = {
            path: (1.0 - damping) * personalization[path]
            + damping * dangling_mass * personalization[path]
            for path in paths
        }

        for src_path in paths:
            outgoing = transitions[src_path]
            if not outgoing:
                continue
            damped_score = damping * scores[src_path]
            for dst_path, probability in outgoing.items():
                next_scores[dst_path] += damped_score * probability

        if sum(abs(next_scores[path] - scores[path]) for path in paths) <= tolerance:
            scores = next_scores
            break
        scores = next_scores

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return RankResult(
        items=[path for path, _ in ranked],
        scores=[score for _, score in ranked],
    )


def recall_at_k(items: list[str], gold_items: list[str], k: int) -> float:
    _validate_non_negative_integer("k", k)
    if k == 0 or not gold_items:
        return 0.0
    gold = set(gold_items)
    return len(set(items[:k]) & gold) / len(gold)


def ndcg_at_k(items: list[str], gold_items: list[str], k: int) -> float:
    _validate_non_negative_integer("k", k)
    if k == 0 or not gold_items:
        return 0.0

    gold = set(gold_items)
    dcg = 0.0
    for index, item in enumerate(items[:k]):
        if item in gold:
            dcg += 1.0 / math.log2(index + 2)

    ideal_hits = min(k, len(gold))
    if ideal_hits == 0:
        return 0.0

    ideal_dcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / ideal_dcg


def structure_map_markdown(
    query: str,
    file_graph: FileGraph,
    selected_files: list[str],
    *,
    max_files: int = 5,
    max_neighbors_per_kind: int = 5,
    n_anchors: int = 3,
) -> str:
    _validate_non_negative_integer("max_files", max_files)
    _validate_non_negative_integer("max_neighbors_per_kind", max_neighbors_per_kind)
    _validate_positive_integer("n_anchors", n_anchors)

    lexical = lexical_rank(query, file_graph)
    anchors = _top_anchors(lexical, n_anchors)
    visible_paths = {node.path for node in file_graph.nodes}
    files = [path for path in selected_files if path in visible_paths][:max_files]

    lines = [
        f"Query: {_format_code_span(query)}",
        f"Anchors: {_format_code_list(anchors) if anchors else '_none_'}",
        f"Selected Files: {_format_code_list(files) if files else '_none_'}",
    ]

    for path in files:
        lines.append("")
        lines.append(f"### {_format_code_span(path)}")
        grouped_neighbors: dict[str, list[str]] = defaultdict(list)
        for neighbor in file_graph.adjacency.get(path, []):
            for label in file_graph.edge_labels.get((path, neighbor), ()):
                grouped_neighbors[_EDGE_GROUP_NAMES.get(label, label)].append(neighbor)

        for group_name in _EDGE_GROUP_ORDER:
            neighbors = sorted(set(grouped_neighbors.get(group_name, ())))[:max_neighbors_per_kind]
            if not neighbors:
                continue
            lines.append(f"- {group_name}: {_format_code_list(neighbors)}")

    return "\n".join(lines)


def _lexical_score(node, query_tokens: set[str]) -> int:
    if not query_tokens:
        return 0
    path_tokens = set(tokenize_identifier(node.path))
    basename_tokens = set(tokenize_identifier(node.name))
    text_tokens = set(tokenize_identifier(node.text))
    return (
        len(query_tokens & path_tokens)
        + len(query_tokens & basename_tokens)
        + len(query_tokens & text_tokens)
    )


def _top_anchors(lexical: RankResult, n_anchors: int) -> list[str]:
    if n_anchors <= 0:
        return []

    paired = list(zip(lexical.items, lexical.scores))
    positive = [path for path, score in paired if score > 0][:n_anchors]
    if positive:
        return positive
    return [path for path, _ in paired[:n_anchors]]


def _personalization(paths: list[str], anchors: list[str]) -> dict[str, float]:
    if not paths:
        return {}
    if not anchors:
        mass = 1.0 / len(paths)
        return {path: mass for path in paths}

    anchor_mass = 1.0 / len(anchors)
    return {path: (anchor_mass if path in anchors else 0.0) for path in paths}


def _build_transitions(
    paths: list[str],
    file_graph: FileGraph,
) -> dict[str, dict[str, float]]:
    transitions: dict[str, dict[str, float]] = {}
    for path in paths:
        weights = {
            neighbor: _validated_edge_weight(
                file_graph.weights[(path, neighbor)],
                f"{path}->{neighbor}",
            )
            for neighbor in file_graph.adjacency.get(path, [])
            if (path, neighbor) in file_graph.weights
        }
        if weights:
            weights[path] = _CONNECTED_SELF_LOOP_WEIGHT
            total = sum(weights.values())
            transitions[path] = {
                neighbor: weight / total
                for neighbor, weight in weights.items()
            }
        else:
            transitions[path] = {}
    return transitions


def _format_code_list(values: list[str]) -> str:
    return ", ".join(_format_code_span(value) for value in values)


def _format_code_span(value: str) -> str:
    longest_run = max((len(match.group(0)) for match in re.finditer(r"`+", value)), default=0)
    delimiter = "`" * (longest_run + 1)
    return f"{delimiter}{value}{delimiter}"


def _validated_edge_weight(weight: float, context: str) -> float:
    numeric_weight = float(weight)
    if not math.isfinite(numeric_weight) or numeric_weight <= 0.0:
        raise ValueError(
            f"edge weight must be finite and positive for {context}: {weight!r}"
        )
    return numeric_weight


def _validate_non_negative_integer(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _validate_positive_integer(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_non_negative_number(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _validate_damping(value: float) -> None:
    if value < 0.0 or value >= 1.0:
        raise ValueError("damping must be in [0, 1)")
