"""Run the AI code review experiment."""

from __future__ import annotations

import argparse
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

from src.context import (
    build_selective_context_fn,
    chunk_repository,
    full_repository_context,
)
from src.data import SAMPLE_PRS, TOY_REPOSITORY
from src.evaluation import evaluate_ensemble, evaluate_reviewer


def configure_tls_trust_store():
    try:
        import truststore
    except ImportError:
        return

    truststore.inject_into_ssl()


def load_environment():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        load_dotenv(override=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AI code review reviewer comparisons.")
    parser.add_argument(
        "--mode",
        choices=["all", "diff", "full", "selective", "ensemble"],
        default="all",
        help="Reviewer implementation to run.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N PRs.")
    parser.add_argument("--model", default="gpt-4o-mini", help="Chat model for review calls.")
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-large",
        help="Embedding model for selective context retrieval.",
    )
    parser.add_argument("--n-results", type=int, default=10, help="Retrieved chunks per PR.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate fixtures and print counts without calling OpenAI APIs.",
    )
    return parser.parse_args()


def selected_prs(limit: int | None) -> list[dict]:
    return SAMPLE_PRS[:limit] if limit else SAMPLE_PRS


def print_metrics(name: str, result: dict):
    metrics = result["metrics"]
    print(
        f"{name}: "
        f"precision={metrics['precision']:.2%}, "
        f"recall={metrics['recall']:.2%}, "
        f"f1={metrics['f1']:.2%}, "
        f"tp={metrics['true_positives']}, "
        f"fp={metrics['false_positives']}, "
        f"fn={metrics['false_negatives']}"
    )


def run_benchmark(args: argparse.Namespace) -> dict[str, dict]:
    from openai import OpenAI

    prs = selected_prs(args.limit)
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    results: dict[str, dict] = {}
    selective_context_fn = None

    if args.mode in {"all", "selective", "ensemble"}:
        selective_context_fn = build_selective_context_fn(
            TOY_REPOSITORY,
            openai_client=openai_client,
            embedding_model=args.embedding_model,
            n_results=args.n_results,
        )

    if args.mode in {"all", "diff"}:
        results["Diff-only"] = evaluate_reviewer(
            prs,
            openai_client=openai_client,
            model=args.model,
            context_fn=None,
        )

    if args.mode in {"all", "full"}:
        results["Full context"] = evaluate_reviewer(
            prs,
            openai_client=openai_client,
            model=args.model,
            context_fn=full_repository_context(TOY_REPOSITORY),
        )

    if args.mode in {"all", "selective"}:
        results["Selective context"] = evaluate_reviewer(
            prs,
            openai_client=openai_client,
            model=args.model,
            context_fn=selective_context_fn,
        )

    if args.mode in {"all", "ensemble"}:
        results["Specialized ensemble"] = evaluate_ensemble(
            prs,
            openai_client=openai_client,
            model=args.model,
            context_fn=selective_context_fn,
        )

    return results


def main():
    configure_tls_trust_store()
    load_environment()
    args = parse_args()

    chunks = chunk_repository(TOY_REPOSITORY)
    prs = selected_prs(args.limit)

    if args.dry_run:
        print(f"repository_files={len(TOY_REPOSITORY)}")
        print(f"repository_chunks={len(chunks)}")
        print(f"pull_requests={len(prs)}")
        print(f"mode={args.mode}")
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required. Set it in the environment or .env.")

    for name, result in run_benchmark(args).items():
        print_metrics(name, result)


if __name__ == "__main__":
    main()
