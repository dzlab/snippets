"""Render the source-backed SVG figures used by the code-graph article.

The renderer intentionally uses only the Python standard library.  It consumes
the portable SQLite index, an explicit task file, and the committed Django
benchmark JSON; it never calls an API or embeds external resources.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from codekg.retrieval import graph_rank, lexical_rank
from codekg.store import load_file_graph, open_store


WIDTH = 960
BLUE = "#2563eb"
PURPLE = "#7c3aed"
TEAL = "#0f766e"
AMBER = "#b45309"
SLATE = "#475569"
LIGHT = "#f8fafc"
GRID = "#cbd5e1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--django", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--query", default="PGN import worker")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    connection = open_store(args.db)
    try:
        file_graph = load_file_graph(connection)
        tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
        experiment = json.loads(args.experiment.read_text(encoding="utf-8"))
        django = json.loads(args.django.read_text(encoding="utf-8"))
        if len(tasks) != len(experiment.get("tasks", [])):
            raise ValueError("task file and experiment result contain different task counts")
        _write(args.output_dir / "20260830-code-kg-file-graph.svg", render_file_graph(file_graph, args.query))
        _write(
            args.output_dir / "20260830-code-kg-retrieval.svg",
            render_retrieval(file_graph, experiment, args.query),
        )
        _write(
            args.output_dir / "20260830-code-kg-django-workflow.svg",
            render_django_workflow(django),
        )
    finally:
        connection.close()
    return 0


def render_file_graph(file_graph, query: str) -> str:
    lexical = lexical_rank(query, file_graph)
    graph = graph_rank(query, file_graph, n_anchors=3)
    anchors = lexical.items[:3]
    selected = []
    for path in graph.items[:12] + anchors:
        if path not in selected:
            selected.append(path)
    selected = selected[:14]
    center_x, center_y = 480, 285
    positions = {}
    radius_x, radius_y = 340, 185
    for index, path in enumerate(selected):
        angle = -math.pi / 2 + (2 * math.pi * index / max(1, len(selected)))
        positions[path] = (center_x + radius_x * math.cos(angle), center_y + radius_y * math.sin(angle))

    edges = []
    seen = set()
    for source in selected:
        for target in file_graph.adjacency.get(source, []):
            if target not in positions:
                continue
            key = tuple(sorted((source, target)))
            if key in seen:
                continue
            seen.add(key)
            labels = file_graph.edge_labels.get((source, target), ())
            edges.append((source, target, labels[0] if labels else "related"))

    parts = _svg_header("Chess Studio file graph", 720)
    parts.append(_text(40, 42, "Chess Studio · bounded file-level graph", 24, "#0f172a", bold=True))
    parts.append(_text(40, 70, f"Query: {query} · 3 lexical anchors · {len(selected)} ranked files shown", 14, SLATE))
    parts.append(_text(40, 98, "The database contains 532 files; this view shows the query-relevant PageRank neighborhood.", 13, SLATE))
    for source, target, label in edges:
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        parts.append(_line(x1, y1, x2, y2, _edge_color(label), 2))
    for index, path in enumerate(selected):
        x, y = positions[path]
        is_anchor = path in anchors
        fill = BLUE if is_anchor else PURPLE if index < 12 else TEAL
        parts.append(_circle(x, y, 30 if is_anchor else 25, fill))
        parts.append(_text(x, y + 5, str(index + 1), 15, "white", anchor="middle", bold=True))
        parts.extend(_path_label(x, y + 48, path, 13))
    parts.append(_text(40, 650, "Blue = lexical anchor   Purple = graph-ranked file   Teal = additional anchor", 13, SLATE))
    parts.append(_legend(40, 682, [("imports / calls", BLUE), ("co-edit history", AMBER), ("ranked file", PURPLE)]))
    return "".join(parts) + "</svg>\n"


def render_retrieval(file_graph, experiment: dict, query: str) -> str:
    lexical = lexical_rank(query, file_graph)
    graph = graph_rank(query, file_graph, n_anchors=3)
    top_n = 7
    parts = _svg_header("Keyword versus PageRank", 800)
    parts.append(_text(40, 42, "Keyword search versus personalized PageRank", 24, "#0f172a", bold=True))
    parts.append(_text(40, 70, f"Chess Studio query: {query} · PageRank is seeded by the top three lexical anchors", 14, SLATE))
    parts.extend(_rank_column(55, 105, "Keyword overlap", lexical.items[:top_n], BLUE))
    parts.extend(_rank_column(505, 105, "Personalized PageRank", graph.items[:top_n], PURPLE))
    parts.append(_text(40, 420, "Offline localization on three explicit chess-studio tasks", 18, "#0f172a", bold=True))
    parts.append(_text(40, 448, "Recall is the fraction of gold files found in the first k results; these are new repository-specific results.", 13, SLATE))
    metric_x = {1: 190, 3: 410, 5: 630}
    for k, x in metric_x.items():
        parts.append(_text(x, 485, f"recall@{k}", 13, SLATE, anchor="middle"))
    for row_index, task in enumerate(experiment.get("tasks", [])):
        y = 525 + row_index * 62
        label = _short_task(task.get("query", f"task {row_index + 1}"))
        parts.append(_text(40, y + 5, label, 12, "#0f172a"))
        for k, x in metric_x.items():
            lexical_value = task.get("lexical", {}).get(f"recall_at_{k}", 0.0)
            graph_value = task.get("graph", {}).get(f"recall_at_{k}", 0.0)
            parts.append(_bar(x - 42, y + 14, 84, 14, lexical_value, BLUE, f"K {lexical_value:.2f}"))
            parts.append(_bar(x - 42, y + 32, 84, 14, graph_value, PURPLE, f"P {graph_value:.2f}"))
    parts.append(_legend(40, 735, [("keyword", BLUE), ("PageRank", PURPLE)]))
    return "".join(parts) + "</svg>\n"


def render_django_workflow(result: dict) -> str:
    aggregate = result["aggregate"]
    control = aggregate["control"]
    treatment = aggregate["treatment"]
    metrics = [
        ("time", "mean_duration_ms", True),
        ("tokens", "mean_total_tokens", True),
        ("tool calls", "mean_tool_calls", True),
        ("first edit", "mean_tool_calls_to_first_correct_edit", True),
        ("cost", "mean_cost_usd", True),
    ]
    parts = _svg_header("Django workflow benchmark", 590)
    parts.append(_text(40, 42, "Django coding-workflow case study", 24, "#0f172a", bold=True))
    parts.append(_text(40, 70, "Five runs per arm · structure-map treatment versus bare-repository control", 14, SLATE))
    parts.append(_text(40, 98, "Treatment shown as a percentage of control (lower is better). Correctness: 100% in both arms.", 13, SLATE))
    chart_left, chart_top, chart_width, chart_height = 80, 145, 820, 300
    parts.append(_line(chart_left, chart_top + chart_height, chart_left + chart_width, chart_top + chart_height, GRID, 1))
    for tick in (0, 25, 50, 75, 100, 125):
        x = chart_left + chart_width * tick / 125
        parts.append(_line(x, chart_top, x, chart_top + chart_height, GRID, 1, dash="4 4"))
        parts.append(_text(x, chart_top + chart_height + 22, str(tick), 12, SLATE, anchor="middle"))
    for index, (label, field, _lower_is_better) in enumerate(metrics):
        y = chart_top + 25 + index * 53
        control_value = float(control[field])
        treatment_value = float(treatment[field])
        ratio = 100 * treatment_value / control_value if control_value else 0
        parts.append(_text(40, y + 8, label, 13, "#0f172a", anchor="start"))
        parts.append(_bar(chart_left, y - 7, chart_width * 100 / 125, 17, 1.0, SLATE, "control 100%", absolute=True))
        parts.append(_bar(chart_left, y + 14, chart_width / 125, 17, ratio / 100, TEAL, f"{ratio:.1f}%", absolute=True))
    parts.append(_legend(40, 490, [("control", SLATE), ("structure map", TEAL)]))
    parts.append(_text(40, 535, "Hero task: Django cache-control directive matching. The broader ten-task suite was mixed and not statistically conclusive.", 12, SLATE))
    return "".join(parts) + "</svg>\n"


def _svg_header(title: str, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{html.escape(title)}</title>",
        f'<desc id="desc">Source-backed visualization generated from the chess-studio code graph and the Django benchmark data.</desc>',
        f'<rect width="{WIDTH}" height="{height}" fill="{LIGHT}"/>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif} .path{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}</style>',
    ]


def _text(x, y, value, size, fill, anchor="start", bold=False):
    weight = " font-weight=\"700\"" if bold else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{weight}>{html.escape(str(value))}</text>'


def _line(x1, y1, x2, y2, stroke, width, dash=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def _circle(x, y, radius, fill):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="white" stroke-width="3"/>'


def _path_label(x, y, path, size):
    path = path.replace("packages/", "pkg/")
    pieces = path.split("/")
    first = "/".join(pieces[:-1]) + "/" if len(pieces) > 1 else ""
    last = pieces[-1]
    return [_text(x, y, first, size - 1, SLATE, anchor="middle"), _text(x, y + size + 2, last, size, "#0f172a", anchor="middle", bold=True)]


def _edge_color(label):
    return AMBER if label == "co_edit" else BLUE if label in {"import", "call"} else GRID


def _legend(x, y, entries):
    parts = []
    cursor = x
    for label, color in entries:
        parts.append(f'<rect x="{cursor}" y="{y - 11}" width="12" height="12" fill="{color}"/>')
        parts.append(_text(cursor + 18, y, label, 12, SLATE))
        cursor += 100 + len(label) * 3
    return "".join(parts)


def _rank_column(x, y, title, items, color):
    parts = [_text(x, y, title, 18, "#0f172a", bold=True)]
    for index, path in enumerate(items):
        row_y = y + 38 + index * 34
        parts.append(f'<rect x="{x}" y="{row_y - 21}" width="390" height="27" rx="4" fill="white" stroke="#e2e8f0"/>')
        parts.append(_text(x + 14, row_y - 3, str(index + 1), 12, color, bold=True))
        parts.append(_text(x + 42, row_y - 3, path.replace("packages/", "pkg/"), 11, "#0f172a"))
    return parts


def _bar(x, y, width, height, value, color, label, absolute=False):
    fill_width = width * value if absolute else width * max(0.0, min(1.0, value))
    parts = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height}" fill="#e2e8f0" rx="3"/>']
    parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{fill_width:.1f}" height="{height}" fill="{color}" rx="3"/>')
    parts.append(_text(x + fill_width + 7, y + height - 3, label, 11, SLATE))
    return "".join(parts)


def _short_task(query: str) -> str:
    words = query.replace("Where is ", "").replace("Where are ", "").rstrip("?").split()
    return " ".join(words[:5]) + (" …" if len(words) > 5 else "")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
