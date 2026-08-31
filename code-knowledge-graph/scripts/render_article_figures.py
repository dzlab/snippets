"""Render article figures with the same Matplotlib/NetworkX style as L4.

The core ``codekg`` CLI remains dependency-free. Install the optional figure
dependencies first, for example ``uv run --with matplotlib --with networkx``.
The renderer consumes the portable SQLite index and an explicit task file; it
never calls an API or embeds external data.
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
    if len(tasks) != len(experiment.get("tasks", [])):
        raise ValueError("task file and experiment result contain different task counts")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "20260830-code-kg-full-graph.png": render_repository_graph(nodes, edges),
        "20260830-code-kg-file-layer.png": render_file_layer_graph(nodes, edges),
        "20260830-code-kg-anchor-walk.png": render_anchor_walk(nodes, edges, args.query),
        "20260830-code-kg-retrieval-comparison.png": render_retrieval_comparison(experiment),
        "20260830-code-kg-chess-studio-benchmark.png": render_chess_studio_benchmark(experiment),
    }
    for filename, figure in figures.items():
        save_figure(figure, args.output_dir / filename)
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
    """Render the notebook's whole repository graph as one chart."""
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

    fig, ax = plt.subplots(figsize=(18, 13))
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

    fig.suptitle("Chess Studio repository graph rendered with the L4 NetworkX/Matplotlib style", fontsize=15, y=0.98)
    fig.tight_layout()
    return fig


def render_file_layer_graph(nodes: list[dict], edges: list[tuple[str, str, str]]):
    """Render the notebook-style readable file-layer hub view as one chart."""
    import matplotlib.pyplot as plt

    graph, _ = _file_graph(nodes, edges)
    fig, ax = plt.subplots(figsize=(13, 11))
    _render_file_zoom(ax, graph)
    ax.set_title(
        "Chess Studio file-layer hub neighborhood\n"
        "core files are colored by dominant relationship; ghost files show the surrounding context",
        fontsize=12,
    )
    fig.tight_layout()
    return fig


def render_anchor_walk(
    nodes: list[dict], edges: list[tuple[str, str, str]], query: str
):
    """Render an L4-style anchor walk for a real chess-studio query."""
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.lines import Line2D

    walk_graph, anchor, reached = _anchor_walk_context(nodes, edges, query)
    layout = nx.spring_layout(walk_graph, seed=23, k=2.0)

    fig, ax = plt.subplots(figsize=(13, 9))
    for source, target, data in walk_graph.edges(data=True):
        kinds = data.get("kinds", {"co_edit"})
        kind = next((candidate for candidate in ("contains", "import", "call", "co_edit") if candidate in kinds), "co_edit")
        style = EDGE_STYLE[kind]
        nx.draw_networkx_edges(
            walk_graph, layout, edgelist=[(source, target)], ax=ax,
            arrows=False, width=style["lw"],
            style=style["ls"], edge_color=style["color"], alpha=0.35,
        )
    nx.draw_networkx_nodes(
        walk_graph, layout, nodelist=list(walk_graph), node_shape="s", node_size=620,
        node_color=NODE_FILL, edgecolors="white", ax=ax,
    )
    nx.draw_networkx_nodes(walk_graph, layout, nodelist=[anchor], node_shape="s", node_size=950, node_color=NODE_FILL, edgecolors="#D55E00", linewidths=3, ax=ax)
    reached_nodes = [node for node in reached if node in walk_graph]
    nx.draw_networkx_nodes(
        walk_graph, layout, nodelist=reached_nodes, node_shape="s", node_size=700,
        node_color=NODE_FILL, edgecolors="#0072B2", linewidths=2.5, ax=ax,
    )
    labels = {node: _display_label(node) for node in walk_graph}
    nx.draw_networkx_labels(walk_graph, layout, labels, font_size=8, ax=ax)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="s", color="none", markerfacecolor="none", markeredgecolor="#D55E00", markeredgewidth=2.5, markersize=11, label="anchor — keyword match"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor="none", markeredgecolor="#0072B2", markeredgewidth=2.5, markersize=10, label="reached by PageRank walk"),
            Line2D([0], [0], color=EDGE_STYLE["import"]["color"], lw=2, label="import"),
            Line2D([0], [0], color=EDGE_STYLE["co_edit"]["color"], lw=2, ls="--", label="co_edit"),
        ], loc="upper left", fontsize=9, framealpha=0.9,
    )
    ax.set_title(
        f'Anchor walk for "{query}"\n'
        f"{len(walk_graph)} files in the top PageRank neighborhood",
        fontsize=12,
    )
    ax.axis("off")
    fig.tight_layout()
    return fig


def render_retrieval_comparison(experiment: dict):
    """Render one aggregate keyword-versus-PageRank recall chart."""
    import matplotlib.pyplot as plt

    aggregate = experiment.get("aggregate", {})
    ks = [1, 3, 5]
    keyword = [aggregate.get("lexical", {}).get(f"recall_at_{k}", 0.0) for k in ks]
    pagerank = [aggregate.get("graph", {}).get(f"recall_at_{k}", 0.0) for k in ks]
    fig, ax = plt.subplots(figsize=(11, 7))
    import numpy as np

    x = np.arange(len(ks))
    width = 0.34
    bars_keyword = ax.bar(x - width / 2, keyword, width, color="#0072B2", label="keyword")
    bars_pagerank = ax.bar(x + width / 2, pagerank, width, color="#D55E00", label="PageRank")
    for bars in (bars_keyword, bars_pagerank):
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.025,
                f"{bar.get_height():.2f}",
                ha="center",
                fontsize=9,
            )
    ax.set_xticks(x)
    ax.set_xticklabels([f"recall@{k}" for k in ks])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("mean recall across three chess-studio tasks")
    ax.set_title(
        "Chess Studio retrieval: keyword search versus PageRank\n"
        "PageRank is seeded by lexical anchors; this is an offline three-task sample",
        fontsize=12,
    )
    ax.legend(framealpha=0.9)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def render_chess_studio_benchmark(experiment: dict):
    """Render one task-level recall chart from the real repository experiment."""
    import matplotlib.pyplot as plt
    import numpy as np

    tasks = experiment.get("tasks", [])
    labels = [f"task {index + 1}" for index in range(len(tasks))]
    keyword = [task.get("lexical", {}).get("recall_at_5", 0.0) for task in tasks]
    pagerank = [task.get("graph", {}).get("recall_at_5", 0.0) for task in tasks]
    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(11, 7))
    bars_keyword = ax.bar(x - width / 2, keyword, width, color="#0072B2", label="keyword")
    bars_pagerank = ax.bar(x + width / 2, pagerank, width, color="#D55E00", label="PageRank")
    for bars in (bars_keyword, bars_pagerank):
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.025,
                f"{bar.get_height():.2f}",
                ha="center",
                fontsize=9,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("recall@5")
    ax.set_title(
        "Chess Studio task-level retrieval at recall@5\n"
        "three explicit queries with repository-relative gold files",
        fontsize=12,
    )
    ax.legend(framealpha=0.9)
    ax.grid(axis="y", alpha=0.25)
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


def _anchor_walk_context(nodes, edges, query):
    import networkx as nx

    graph, file_metadata = _file_graph(nodes, edges)
    query_tokens = _tokens(query)
    lexical_scores = {
        node: _file_lexical_score(query_tokens, file_metadata[node])
        for node in graph
    }
    anchors = sorted(lexical_scores, key=lambda node: (-lexical_scores[node], node))[:3]
    anchor = anchors[0]
    ppr = nx.pagerank(graph, alpha=0.85, personalization={anchor: 1.0}, max_iter=100)
    ranked = [node for node, _ in sorted(ppr.items(), key=lambda item: (-item[1], item[0]))]
    shown = set(ranked[:18]) | {anchor}
    walk_graph = graph.subgraph(shown).copy()
    reached = [node for node in ranked if node != anchor][:5]
    return walk_graph, anchor, reached


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
