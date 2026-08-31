"""Render article figures with the same Matplotlib/NetworkX style as L4.

The core ``codekg`` CLI remains dependency-free. Install the optional figure
dependencies first, for example ``uv run --with matplotlib --with networkx``.
The renderer consumes the portable SQLite index, an explicit task file, and a
committed Django benchmark JSON; it never calls an API or embeds external data.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path


DEP_COLOR = "#5b6770"
CO_COLOR = "#0072B2"
NODE_FILL = "#7a838d"
EDGE_STYLE = {
    "contains": {"color": "#8a8f98", "ls": "-", "lw": 1.2},
    "import": {"color": "#0072B2", "ls": "-", "lw": 1.8},
    "call": {"color": "#D55E00", "ls": ":", "lw": 1.8},
    "co_edit": {"color": "#009E73", "ls": "--", "lw": 1.8},
}
GHOST_NODE = "#c9cdd2"
EDGE_KIND_MAP = {"imports": "import", "calls": "call"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--django", type=Path, required=True)
    parser.add_argument("--django-suite", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--query", default="PGN import worker")
    args = parser.parse_args()

    import matplotlib

    matplotlib.use("Agg")
    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    try:
        nodes, edges = load_graph(connection)
    finally:
        connection.close()

    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    experiment = json.loads(args.experiment.read_text(encoding="utf-8"))
    django = json.loads(args.django.read_text(encoding="utf-8"))
    django_suite = json.loads(args.django_suite.read_text(encoding="utf-8"))
    if len(tasks) != len(experiment.get("tasks", [])):
        raise ValueError("task file and experiment result contain different task counts")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    save_figure(render_repository_graph(nodes, edges), args.output_dir / "20260830-code-kg-file-graph.png")
    save_figure(
        render_retrieval_comparison(nodes, edges, experiment, args.query),
        args.output_dir / "20260830-code-kg-retrieval.png",
    )
    save_figure(
        render_django_benchmark(django, django_suite),
        args.output_dir / "20260830-code-kg-django-workflow.png",
    )
    return 0


def load_graph(connection: sqlite3.Connection) -> tuple[list[dict], list[tuple[str, str, str]]]:
    nodes = [dict(row) for row in connection.execute(
        "SELECT id, kind, path, name, text FROM nodes ORDER BY id"
    )]
    edges = []
    for row in connection.execute("SELECT src, dst, kind FROM edges ORDER BY src, dst, kind"):
        edges.append((row[0], row[1], EDGE_KIND_MAP.get(row[2], row[2])))
    return nodes, edges


def render_repository_graph(nodes: list[dict], edges: list[tuple[str, str, str]]):
    """Render the notebook's whole-graph plus readable file-layer zoom."""
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.lines import Line2D

    graph = _collapsed_graph(nodes, edges)
    layout = nx.spring_layout(graph, seed=1, k=0.55, iterations=80)
    degree = dict(graph.degree())
    node_color = {node: _dominant_color(graph, node) for node in graph}
    node_shape = {node: ("s" if node.startswith("file:") else "^") for node in graph}
    max_degree = max(degree.values(), default=1)
    node_size = {
        node: (1.4 if node.startswith("file:") else 0.7)
        + (1.6 if degree[node] >= max(8, max_degree * 0.25) else 0)
        for node in graph
    }

    fig, axes = plt.subplots(1, 2, figsize=(24, 13), gridspec_kw={"width_ratios": (1.05, 1)})
    ax = axes[0]
    nx.draw_networkx_edges(graph, layout, edge_color="#aab0b8", width=0.35, alpha=0.55, ax=ax)
    for shape in ("^", "s"):
        group = [node for node in graph if node_shape[node] == shape]
        nx.draw_networkx_nodes(
            graph, layout, nodelist=group, node_shape=shape,
            node_size=[node_size[node] * 60 for node in group],
            node_color=[node_color[node] for node in group], linewidths=0, ax=ax,
        )
    legend = [
        _key("s", DEP_COLOR, "file - dependency-led (import/call)"),
        _key("s", CO_COLOR, "file - co_edit-led (changed together)"),
        _key("^", DEP_COLOR, "symbol/function - dependency-led"),
        _key("^", CO_COLOR, "symbol/function - co_edit-led"),
        Line2D([0], [0], color="#aab0b8", lw=1.4, label="edge (import / call / co_edit)"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_title(
        f"Chess Studio code graph ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} collapsed visual edges)\n"
        "shape = node type   |   colour = dominant relationship   |   bigger = hub",
        fontsize=12,
    )
    ax.axis("off")

    _render_file_zoom(axes[1], graph)
    fig.suptitle("Repository graph views rendered with the L4 NetworkX/Matplotlib style", fontsize=15, y=0.98)
    fig.tight_layout()
    return fig


def render_retrieval_comparison(
    nodes: list[dict], edges: list[tuple[str, str, str]], experiment: dict, query: str
):
    """Render an L4-style anchor walk beside a keyword/PageRank scorecard."""
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.lines import Line2D

    graph, file_metadata = _file_graph(nodes, edges)
    file_nodes = list(graph)
    query_tokens = _tokens(query)
    lexical_scores = {
        node: _file_lexical_score(query_tokens, file_metadata[node])
        for node in file_nodes
    }
    anchors = [node for node, _ in sorted(lexical_scores.items(), key=lambda item: (-item[1], item[0]))[:3]]
    anchor = anchors[0]
    ppr = nx.pagerank(graph, alpha=0.85, personalization={anchor: 1.0}, max_iter=100)
    ranked = [node for node, _ in sorted(ppr.items(), key=lambda item: (-item[1], item[0]))]
    shown = set(ranked[:18]) | {anchor}
    walk_graph = graph.subgraph(shown).copy()
    reached = [node for node in ranked if node != anchor][:5]
    layout = nx.spring_layout(walk_graph, seed=23, k=2.0)

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(19, 9), gridspec_kw={"width_ratios": (1.15, 1)})
    for source, target, data in walk_graph.edges(data=True):
        kinds = data.get("kinds", {"co_edit"})
        kind = next((candidate for candidate in ("contains", "import", "call", "co_edit") if candidate in kinds), "co_edit")
        style = EDGE_STYLE[kind]
        nx.draw_networkx_edges(
            walk_graph, layout, edgelist=[(source, target)], ax=ax_left,
            arrows=False, width=style["lw"],
            style=style["ls"], edge_color=style["color"], alpha=0.35,
        )
    nx.draw_networkx_nodes(
        walk_graph, layout, nodelist=list(walk_graph), node_shape="s", node_size=620,
        node_color=NODE_FILL, edgecolors="white", ax=ax_left,
    )
    nx.draw_networkx_nodes(walk_graph, layout, nodelist=[anchor], node_shape="s", node_size=950, node_color=NODE_FILL, edgecolors="#D55E00", linewidths=3, ax=ax_left)
    reached_nodes = [node for node in reached if node in walk_graph]
    nx.draw_networkx_nodes(
        walk_graph, layout, nodelist=reached_nodes, node_shape="s", node_size=700,
        node_color=NODE_FILL, edgecolors="#0072B2", linewidths=2.5, ax=ax_left,
    )
    labels = {node: _display_label(node) for node in walk_graph}
    nx.draw_networkx_labels(walk_graph, layout, labels, font_size=7, ax=ax_left)
    ax_left.legend(
        handles=[
            Line2D([0], [0], marker="s", color="none", markerfacecolor="none", markeredgecolor="#D55E00", markeredgewidth=2.5, markersize=11, label="anchor — keyword match"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor="none", markeredgecolor="#0072B2", markeredgewidth=2.5, markersize=10, label="reached by PageRank walk"),
            Line2D([0], [0], color=EDGE_STYLE["import"]["color"], lw=2, label="import"),
            Line2D([0], [0], color=EDGE_STYLE["co_edit"]["color"], lw=2, ls="--", label="co_edit"),
        ], loc="upper left", fontsize=8, framealpha=0.9,
    )
    ax_left.set_title(f'Anchor walk for "{query}"\n{len(walk_graph)} files in the top PageRank neighborhood', fontsize=11)
    ax_left.axis("off")

    _render_recall_scorecard(ax_right, experiment)
    fig.suptitle("Retrieval: keyword anchors first, then graph propagation", fontsize=14, y=0.98)
    fig.tight_layout()
    return fig


def render_django_benchmark(result: dict, suite: dict):
    """Render the notebook's signed hero bars beside its suite spread."""
    import matplotlib.pyplot as plt

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(17, 6.5), gridspec_kw={"width_ratios": (1.15, 1)})
    aggregate = result["aggregate"]
    control, treatment = aggregate["control"], aggregate["treatment"]
    rows = [
        ("Gold recall", "mean_recall", False),
        ("Fewer tokens", "mean_total_tokens", True),
        ("Fewer tool calls", "mean_tool_calls", True),
        ("Faster to first correct edit", "mean_tool_calls_to_first_correct_edit", True),
        ("Less total time", "mean_duration_ms", True),
        ("Lower cost", "mean_cost_usd", True),
    ]
    labels, values = [], []
    for label, key, lower_better in rows:
        change = (treatment[key] - control[key]) / control[key] * 100
        labels.append(label)
        values.append(-change if lower_better else change)
    colors = ["#2e9e5b" if value >= 0 else "#c0392b" for value in values]
    ax_left.bar(range(len(labels)), values, color=colors)
    ax_left.axhline(0, color="#333", lw=0.9)
    ax_left.set_xticks(range(len(labels)))
    ax_left.set_xticklabels(labels, rotation=28, ha="right", fontsize=8)
    ax_left.set_ylabel("improvement % (positive = structure map better)")
    ax_left.set_title("Django cache-control hero task (n=5/arm)", fontsize=11)
    ax_left.grid(axis="y", alpha=0.25)
    for index, value in enumerate(values):
        ax_left.text(index, value + (1.5 if value >= 0 else -3), f"{value:+.0f}%", ha="center", fontsize=8, fontweight="bold")

    suite_rows = sorted(suite.get("per_task", []), key=lambda row: row.get("metrics", {}).get("mean_duration_ms", {}).get("pct_improvement", 0))
    suite_labels = [row["task"].replace("django_", "") for row in suite_rows]
    suite_values = [row["metrics"]["mean_duration_ms"]["pct_improvement"] for row in suite_rows]
    suite_colors = ["#c0392b" if value < 0 else "#d9a441" if value < 4 else "#2e9e5b" for value in suite_values]
    ax_right.barh(range(len(suite_labels)), suite_values, color=suite_colors)
    ax_right.axvline(0, color="#333", lw=0.9)
    ax_right.set_yticks(range(len(suite_labels)))
    ax_right.set_yticklabels(suite_labels, fontsize=8)
    ax_right.set_xlabel("total-time improvement % (positive = graph faster)")
    pooled = suite.get("pooled", {})
    median = pooled.get("mean_duration_ms", {}).get("pooled_median_pct", 0) if isinstance(pooled, dict) else 0
    ax_right.axvline(median, color="#2e9e5b", lw=1.4, ls="--")
    ax_right.set_title(f"Django suite spread (median {median:+.1f}%)", fontsize=11)
    ax_right.grid(axis="x", alpha=0.25)
    fig.suptitle("Coding-workflow benchmark: signed improvements, same style as L4", fontsize=14, y=0.99)
    fig.tight_layout()
    return fig


def _collapsed_graph(nodes, edges):
    import networkx as nx

    graph = nx.Graph()
    graph.add_nodes_from(node["id"] for node in nodes)
    for source, target, kind in edges:
        if source == target:
            continue
        if graph.has_edge(source, target):
            graph.edges[source, target].setdefault("kinds", set()).add(kind)
        else:
            graph.add_edge(source, target, kinds={kind})
    return graph


def _file_graph(nodes, edges):
    """Project the real node graph to the file layer used by retrieval."""
    import networkx as nx

    metadata = {
        node["id"]: node
        for node in nodes
        if node["kind"] == "file" and node.get("path")
    }
    path_by_node = {
        node["id"]: node.get("path")
        for node in nodes
        if node.get("path")
    }
    graph = nx.Graph()
    graph.add_nodes_from(metadata)
    for source, target, kind in edges:
        source_path = path_by_node.get(source)
        target_path = path_by_node.get(target)
        if not source_path or not target_path or source_path == target_path:
            continue
        source_id = f"file:{source_path}"
        target_id = f"file:{target_path}"
        if source_id not in metadata or target_id not in metadata:
            continue
        if graph.has_edge(source_id, target_id):
            graph.edges[source_id, target_id].setdefault("kinds", set()).add(kind)
        else:
            graph.add_edge(source_id, target_id, kinds={kind})
    return graph, {node_id: metadata[node_id] for node_id in graph}


def _file_lexical_score(query_tokens, node):
    return sum(
        len(query_tokens & _tokens(value or ""))
        for value in (node.get("path"), node.get("name"), node.get("text"))
    )


def _dominant_color(graph, node):
    dependency = co_edit = 0
    for _, _, data in graph.edges(node, data=True):
        kinds = data.get("kinds", set())
        dependency += len({"import", "call"} & kinds)
        co_edit += int("co_edit" in kinds)
    return CO_COLOR if co_edit > dependency else DEP_COLOR


def _render_file_zoom(ax, graph):
    import networkx as nx

    file_graph = graph.subgraph([node for node in graph if node.startswith("file:")]).copy()
    file_graph.remove_nodes_from([node for node in list(file_graph) if file_graph.degree(node) == 0])
    degree = dict(file_graph.degree())
    hubs = sorted(degree, key=degree.get, reverse=True)[:3]
    core = list(hubs)
    candidates = [node for node in file_graph if node not in core]
    candidates.sort(key=lambda node: (sum(file_graph.has_edge(node, hub) for hub in hubs), degree[node]), reverse=True)
    core.extend(candidates[:9])
    core_set = set(core)
    ghosts = [node for node in file_graph if node not in core_set and sum(file_graph.has_edge(node, selected) for selected in core_set) >= 2]
    ghosts = sorted(ghosts, key=degree.get, reverse=True)[:12]
    shown = core + ghosts
    subgraph = file_graph.subgraph(shown).copy()
    positions = nx.spring_layout(subgraph.subgraph(core), seed=7, k=1.8, iterations=120)
    for index, node in enumerate(ghosts):
        angle = index * 2 * math.pi / max(1, len(ghosts))
        positions[node] = (1.15 * math.cos(angle), 1.15 * math.sin(angle))
    nx.draw_networkx_edges(subgraph, positions, edge_color="#aab0b8", width=0.6, alpha=0.55, ax=ax)
    nx.draw_networkx_nodes(subgraph, positions, nodelist=core, node_shape="s", node_size=260, node_color=[_dominant_color(subgraph, node) for node in core], ax=ax)
    nx.draw_networkx_nodes(subgraph, positions, nodelist=ghosts, node_shape="s", node_size=180, node_color=GHOST_NODE, edgecolors="white", ax=ax)
    labels = {node: _short_path(_path(node)) for node in shown}
    nx.draw_networkx_labels(subgraph, positions, labels, font_size=6, ax=ax)
    ax.set_title(f"File-layer hub zoom ({len(core)} core + {len(ghosts)} ghost files)", fontsize=11)
    ax.axis("off")


def _render_recall_scorecard(ax, experiment):
    import numpy as np

    tasks = experiment.get("tasks", [])
    ks = [1, 3, 5]
    x = np.arange(len(tasks))
    width = 0.12
    for offset, k in enumerate(ks):
        lexical = [task.get("lexical", {}).get(f"recall_at_{k}", 0.0) for task in tasks]
        graph = [task.get("graph", {}).get(f"recall_at_{k}", 0.0) for task in tasks]
        ax.bar(x + (offset * 2) * width - 0.25, lexical, width, color="#0072B2", alpha=0.85, label="keyword" if offset == 0 else None)
        ax.bar(x + (offset * 2 + 1) * width - 0.25, graph, width, color="#D55E00", alpha=0.85, label="PageRank" if offset == 0 else None)
    ax.set_xticks(x)
    ax.set_xticklabels([f"task {index + 1}" for index in range(len(tasks))], fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("recall")
    ax.set_title("Same tasks: keyword versus PageRank", fontsize=11)
    ax.legend(fontsize=8, framealpha=0.9)
    ax.grid(axis="y", alpha=0.25)


def _key(marker, color, label):
    from matplotlib.lines import Line2D

    return Line2D([0], [0], marker=marker, color="none", markerfacecolor=color, markersize=10, label=label)


def _path(node):
    return node.removeprefix("file:").removeprefix("symbol:")


def _short_path(path):
    parts = path.split("/")
    return "/".join(parts[-2:]) if len(parts) > 1 else path


def _display_label(node):
    if node.startswith("file:"):
        return _short_path(_path(node))
    return node.removeprefix("symbol:").split(".")[-1]


def _tokens(value):
    import re

    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return {token.lower() for token in re.findall(r"[A-Za-z0-9]+", value.replace("_", " "))}


def save_figure(figure, path: Path) -> None:
    figure.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    import matplotlib.pyplot as plt

    plt.close(figure)


if __name__ == "__main__":
    raise SystemExit(main())
