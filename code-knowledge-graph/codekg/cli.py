from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
from pathlib import Path

from .git_history import co_edit_edges
from .llm import LLMRequestError, LLMResponseError, OpenAICompatibleClient
from .model import ParsedGraph, Task
from .parser import scan_repository
from .retrieval import graph_rank, lexical_rank, recall_at_k, structure_map_markdown
from .store import counts, load_file_graph, open_store, replace_graph

METRIC_KS = (1, 3, 5)
DEFAULT_ANCHORS = 3
DEFAULT_K = 5
DEFAULT_MAX_COMMITS = 500
DEFAULT_MAX_FILES_PER_COMMIT = 50
ARM_ORDER = ("control", "treatment")


class CliError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codekg",
        description="Code knowledge graph command line interface.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Build and persist a repository graph.")
    index_parser.add_argument("repo", help="Repository checkout to scan.")
    index_parser.add_argument("--db", required=True, help="SQLite database path.")
    index_parser.add_argument(
        "--max-commits",
        type=int,
        default=DEFAULT_MAX_COMMITS,
        help="Maximum number of commits to inspect for co-edit edges.",
    )
    index_parser.add_argument(
        "--max-files-per-commit",
        type=int,
        default=DEFAULT_MAX_FILES_PER_COMMIT,
        help="Skip commits touching more than this many files.",
    )
    index_parser.set_defaults(handler=_handle_index)

    retrieve_parser = subparsers.add_parser("retrieve", help="Rank files for a text query.")
    _add_retrieval_arguments(retrieve_parser)
    retrieve_parser.set_defaults(handler=_handle_retrieve)

    map_parser = subparsers.add_parser("map", help="Render a markdown structure map.")
    _add_retrieval_arguments(map_parser)
    map_parser.set_defaults(handler=_handle_map)

    experiment_parser = subparsers.add_parser(
        "experiment",
        help="Run offline lexical and graph ranking against a task file.",
    )
    experiment_parser.add_argument("--db", required=True, help="Indexed SQLite database path.")
    experiment_parser.add_argument("--tasks", required=True, help="Task JSON file path.")
    experiment_parser.add_argument(
        "--anchors",
        type=int,
        default=DEFAULT_ANCHORS,
        help="Number of lexical anchors to use for graph ranking.",
    )
    experiment_parser.set_defaults(handler=_handle_experiment)

    ab_parser = subparsers.add_parser(
        "ab",
        help="Run paired LLM control vs treatment retrieval comparisons.",
    )
    ab_parser.add_argument("--db", required=True, help="Indexed SQLite database path.")
    ab_parser.add_argument("--tasks", required=True, help="Task JSON file path.")
    ab_parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL"),
        help="OpenAI-compatible base URL. Defaults to OPENAI_BASE_URL.",
    )
    ab_parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL"),
        help="Model name to send to the OpenAI-compatible endpoint.",
    )
    ab_parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="OpenAI-compatible API key. Defaults to OPENAI_API_KEY.",
    )
    ab_parser.add_argument("--runs", type=int, default=1, help="Runs per task/arm pair.")
    ab_parser.add_argument("--seed", type=int, default=0, help="Seed for paired arm ordering.")
    ab_parser.add_argument(
        "--k",
        type=int,
        default=DEFAULT_K,
        help="Candidate inventory size passed to the model.",
    )
    ab_parser.add_argument(
        "--anchors",
        type=int,
        default=DEFAULT_ANCHORS,
        help="Number of lexical anchors to use for graph ranking.",
    )
    ab_parser.add_argument(
        "--output",
        help="Optional JSON output file path for the full A/B result payload.",
    )
    ab_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare paired prompts without making network requests.",
    )
    ab_parser.set_defaults(handler=_handle_ab)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except CliError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _add_retrieval_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", required=True, help="Indexed SQLite database path.")
    parser.add_argument("--query", required=True, help="Task or retrieval query.")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Number of files to return.")
    parser.add_argument(
        "--anchors",
        type=int,
        default=DEFAULT_ANCHORS,
        help="Number of lexical anchors to use for graph ranking.",
    )


def _handle_index(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo).expanduser().resolve()
    db_path = Path(args.db).expanduser().resolve()
    _require_directory(repo_path, "repo")
    _validated_positive_integer("--max-commits", args.max_commits)
    _validated_positive_integer("--max-files-per-commit", args.max_files_per_commit)

    parsed_graph = scan_repository(repo_path)
    graph = ParsedGraph(
        nodes=parsed_graph.nodes,
        edges=sorted(
            parsed_graph.edges
            + co_edit_edges(
                repo_path,
                max_commits=args.max_commits,
                max_files_per_commit=args.max_files_per_commit,
            ),
            key=lambda edge: (edge.kind, edge.src, edge.dst, edge.weight),
        ),
        warnings=sorted(parsed_graph.warnings),
    )

    connection = open_store(db_path)
    try:
        replace_graph(connection, graph)
        payload = {
            "repo": str(repo_path),
            "db": str(db_path),
            "counts": counts(connection),
            "warnings": list(graph.warnings),
        }
    finally:
        connection.close()

    _emit_json(payload)
    return 0


def _handle_retrieve(args: argparse.Namespace) -> int:
    query = _validated_query(args.query)
    k = _validated_positive_integer("--k", args.k)
    anchors = _validated_positive_integer("--anchors", args.anchors)
    file_graph = _load_file_graph(args.db)

    lexical = lexical_rank(query, file_graph)
    graph = graph_rank(query, file_graph, n_anchors=anchors)
    payload = {
        "query": query,
        "anchors": _anchors_for_query(query, file_graph, anchors),
        "lexical": _top_rank_payload(lexical, k),
        "graph": _top_rank_payload(graph, k),
    }
    _emit_json(payload)
    return 0


def _handle_map(args: argparse.Namespace) -> int:
    query = _validated_query(args.query)
    k = _validated_positive_integer("--k", args.k)
    anchors = _validated_positive_integer("--anchors", args.anchors)
    file_graph = _load_file_graph(args.db)

    ranked = graph_rank(query, file_graph, n_anchors=anchors)
    markdown = structure_map_markdown(
        query,
        file_graph,
        ranked.items[:k],
        max_files=k,
        n_anchors=anchors,
    )
    print(markdown)
    return 0


def _handle_experiment(args: argparse.Namespace) -> int:
    anchors = _validated_positive_integer("--anchors", args.anchors)
    file_graph = _load_file_graph(args.db)
    tasks = _load_tasks(args.tasks)

    task_rows: list[dict[str, object]] = []
    lexical_metrics_list: list[dict[str, float]] = []
    graph_metrics_list: list[dict[str, float]] = []
    available_file_count = len(file_graph.nodes)

    for index, task in enumerate(tasks):
        lexical = lexical_rank(task.query, file_graph)
        graph = graph_rank(task.query, file_graph, n_anchors=anchors)
        visible_gold = [path for path in task.gold_files if path in {node.path for node in file_graph.nodes}]

        lexical_metrics = _metric_payload(lexical.items, visible_gold, available_file_count)
        graph_metrics = _metric_payload(graph.items, visible_gold, available_file_count)
        lexical_metrics_list.append(lexical_metrics)
        graph_metrics_list.append(graph_metrics)
        task_rows.append(
            {
                "task_index": index,
                "query": task.query,
                "gold_files": visible_gold,
                "lexical": lexical_metrics,
                "graph": graph_metrics,
            }
        )

    payload = {
        "tasks": task_rows,
        "aggregate": {
            "task_count": len(task_rows),
            "lexical": _aggregate_metrics(lexical_metrics_list),
            "graph": _aggregate_metrics(graph_metrics_list),
        },
    }
    _emit_json(payload)
    return 0


def _handle_ab(args: argparse.Namespace) -> int:
    runs = _validated_positive_integer("--runs", args.runs)
    k = _validated_positive_integer("--k", args.k)
    anchors = _validated_positive_integer("--anchors", args.anchors)
    file_graph = _load_file_graph(args.db)
    tasks = _load_tasks(args.tasks)
    file_paths = [node.path for node in file_graph.nodes]
    arm_rng = random.Random(args.seed)

    if not args.dry_run:
        if not args.base_url:
            raise CliError("base URL is required for real requests")
        if not args.model:
            raise CliError("model is required for real requests")
        if not args.api_key:
            raise CliError("API key is required for real requests")
        client = OpenAICompatibleClient(
            base_url=args.base_url,
            model=args.model,
            api_key=args.api_key,
        )
    else:
        client = None

    records: list[dict[str, object]] = []
    for run_index in range(runs):
        for task_index, task in enumerate(tasks):
            query = _validated_query(task.query)
            lexical = lexical_rank(query, file_graph)
            graph = graph_rank(query, file_graph, n_anchors=anchors)
            inventory = _candidate_inventory(lexical.items, graph.items, k)
            structure_map = structure_map_markdown(
                query,
                file_graph,
                inventory,
                max_files=k,
                n_anchors=anchors,
            )
            visible_gold = [path for path in task.gold_files if path in file_paths]
            arm_order = list(ARM_ORDER)
            arm_rng.shuffle(arm_order)

            pair_records: dict[str, dict[str, object]] = {}
            for arm in arm_order:
                response = _run_ab_arm(
                    client=client,
                    task=task,
                    inventory=inventory,
                    structure_map=(structure_map if arm == "treatment" else None),
                    visible_gold=visible_gold,
                    dry_run=args.dry_run,
                    available_file_count=len(file_paths),
                )
                pair_records[arm] = {
                    "task_index": task_index,
                    "run": run_index,
                    "arm": arm,
                    "query": task.query,
                    "inventory": list(inventory),
                    **response,
                }

            for arm in ARM_ORDER:
                records.append(pair_records[arm])

    payload = {
        "dry_run": bool(args.dry_run),
        "seed": args.seed,
        "runs": runs,
        "k": k,
        "anchors": anchors,
        "base_url": args.base_url,
        "model": args.model,
        "records": records,
    }
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_json_text(payload), encoding="utf-8")
    _emit_json(payload)
    return 0


def _run_ab_arm(
    *,
    client: OpenAICompatibleClient | None,
    task: Task,
    inventory: list[str],
    structure_map: str | None,
    visible_gold: list[str],
    dry_run: bool,
    available_file_count: int,
) -> dict[str, object]:
    if dry_run:
        ranked_files: list[str] = []
        usage: dict[str, int] = {}
        error: str | None = None
    else:
        assert client is not None
        try:
            result = client.rank_files(
                task=task.query,
                candidate_paths=inventory,
                structure_map=structure_map,
            )
            ranked_files = list(result.files)
            usage = _coerce_usage(result.usage)
            error = None
        except (LLMRequestError, LLMResponseError) as exc:
            ranked_files = []
            usage = {}
            error = str(exc)

    return {
        "ranked_files": ranked_files,
        "recall": _metric_payload(ranked_files, visible_gold, available_file_count),
        "usage": usage,
        "error": error,
    }


def _load_file_graph(db_path: str | Path):
    db_file = _require_existing_file(Path(db_path).expanduser().resolve(), "db")
    connection = open_store(db_file)
    try:
        return load_file_graph(connection)
    finally:
        connection.close()


def _require_directory(path: Path, label: str) -> Path:
    if not path.exists():
        raise CliError(f"{label} not found: {path}")
    if not path.is_dir():
        raise CliError(f"{label} is not a directory: {path}")
    return path


def _require_existing_file(path: Path, label: str) -> Path:
    if not path.exists():
        raise CliError(f"{label} not found: {path}")
    if not path.is_file():
        raise CliError(f"{label} is not a file: {path}")
    return path


def _validated_query(raw_query: str) -> str:
    query = raw_query.strip()
    if not query:
        raise CliError("query must not be empty")
    return query


def _validated_positive_integer(name: str, value: int) -> int:
    if value <= 0:
        raise CliError(f"{name} must be positive")
    return value


def _anchors_for_query(query: str, file_graph, anchors: int) -> list[str]:
    lexical = lexical_rank(query, file_graph)
    paired = list(zip(lexical.items, lexical.scores))
    positive = [path for path, score in paired if score > 0][:anchors]
    if positive:
        return positive
    return [path for path, _ in paired[:anchors]]


def _top_rank_payload(rank_result, k: int) -> dict[str, object]:
    return {
        "items": list(rank_result.items[:k]),
        "scores": [float(score) for score in rank_result.scores[:k]],
    }


def _candidate_inventory(lexical_items: list[str], graph_items: list[str], k: int) -> list[str]:
    inventory: list[str] = []
    seen: set[str] = set()
    for path in list(graph_items[:k]) + list(lexical_items[:k]):
        if path in seen:
            continue
        seen.add(path)
        inventory.append(path)
    return inventory[:k]


def _load_tasks(tasks_path: str | Path) -> list[Task]:
    task_file = _require_existing_file(Path(tasks_path).expanduser().resolve(), "tasks")
    payload = json.loads(task_file.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise CliError("tasks file must contain a JSON array")

    tasks: list[Task] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise CliError(f"task {index} must be an object")
        query = item.get("query")
        gold_files = item.get("gold_files", [])
        if not isinstance(query, str):
            raise CliError(f"task {index} query must be a string")
        if not isinstance(gold_files, list) or any(not isinstance(path, str) for path in gold_files):
            raise CliError(f"task {index} gold_files must be an array of strings")
        tasks.append(Task(query=_validated_query(query), gold_files=list(gold_files)))
    return tasks


def _metric_payload(items: list[str], gold_items: list[str], available_file_count: int) -> dict[str, float]:
    payload: dict[str, float] = {}
    for metric_k in METRIC_KS:
        bounded_k = min(metric_k, available_file_count)
        payload[f"recall_at_{metric_k}"] = float(recall_at_k(items, gold_items, bounded_k))
    return payload


def _aggregate_metrics(metric_rows: list[dict[str, float]]) -> dict[str, float]:
    if not metric_rows:
        return {f"recall_at_{metric_k}": 0.0 for metric_k in METRIC_KS}

    aggregate: dict[str, float] = {}
    for metric_k in METRIC_KS:
        field = f"recall_at_{metric_k}"
        aggregate[field] = float(
            sum(row[field] for row in metric_rows) / len(metric_rows)
        )
    return aggregate


def _coerce_usage(usage: dict[str, object]) -> dict[str, int]:
    coerced: dict[str, int] = {}
    for key in sorted(usage):
        value = usage[key]
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            coerced[key] = value
    return coerced


def _emit_json(payload: dict[str, object]) -> None:
    print(_json_text(payload))


def _json_text(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
