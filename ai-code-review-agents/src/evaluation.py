"""Evaluation utilities for reviewer outputs."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

from .reviewers import keywords, review, review_ensemble


def issues_match(expected: str, found: str, threshold: float = 0.30) -> bool:
    expected_words = keywords(expected)
    found_words = keywords(found)
    if not expected_words:
        return False

    overlap = expected_words & found_words
    keyword_score = len(overlap) / len(expected_words)

    if expected.lower() in found.lower() or found.lower() in expected.lower():
        keyword_score = max(keyword_score, 0.70)

    return keyword_score >= threshold


def evaluate_review(review_result: dict, expected_issues: list[str]) -> dict:
    found_issues = [finding["issue"] for finding in review_result["findings"]]
    matched_expected = set()
    matched_found = set()

    for expected_idx, expected in enumerate(expected_issues):
        for found_idx, found in enumerate(found_issues):
            if found_idx in matched_found:
                continue
            if issues_match(expected, found):
                matched_expected.add(expected_idx)
                matched_found.add(found_idx)
                break

    return {
        "true_positives": len(matched_expected),
        "false_positives": max(0, len(found_issues) - len(matched_found)),
        "false_negatives": max(0, len(expected_issues) - len(matched_expected)),
        "found_count": len(found_issues),
    }


def calculate_metrics(evaluations: list[dict]) -> dict:
    tp = sum(item["true_positives"] for item in evaluations)
    fp = sum(item["false_positives"] for item in evaluations)
    fn = sum(item["false_negatives"] for item in evaluations)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def evaluate_reviewer(
    prs: list[dict],
    openai_client: "OpenAI",
    model: str,
    context_fn: Callable[[dict], str] | None = None,
) -> dict:
    evaluations = []
    reviews = []

    for pr in prs:
        context = context_fn(pr) if context_fn else None
        result = review(
            pr,
            openai_client=openai_client,
            model=model,
            context=context,
            task_context=pr.get("task_context"),
        )
        reviews.append(result)
        evaluations.append(evaluate_review(result, pr["expected_issues"]))

    return {
        "reviews": reviews,
        "metrics": calculate_metrics(evaluations),
    }


def evaluate_ensemble(
    prs: list[dict],
    openai_client: "OpenAI",
    model: str,
    context_fn: Callable[[dict], str],
) -> dict:
    evaluations = []
    reviews = []

    for pr in prs:
        context = context_fn(pr)
        result = review_ensemble(
            pr,
            openai_client=openai_client,
            model=model,
            context=context,
            task_context=pr.get("task_context", ""),
        )
        reviews.append(result)
        evaluations.append(evaluate_review(result, pr["expected_issues"]))

    return {
        "reviews": reviews,
        "metrics": calculate_metrics(evaluations),
    }
