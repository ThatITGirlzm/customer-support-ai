"""Synthetic tests for retrieval evaluation metrics."""

from __future__ import annotations

import pytest

from ml.retrieval_evaluation import (
    evaluate_ranked_ids,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_precision_recall_and_reciprocal_rank() -> None:
    ranked = ["P2", "P1", "P3"]
    relevant = {"P1", "P3"}

    assert precision_at_k(ranked, relevant, 1) == 0.0
    assert precision_at_k(ranked, relevant, 3) == pytest.approx(2 / 3)
    assert recall_at_k(ranked, relevant, 1) == 0.0
    assert recall_at_k(ranked, relevant, 3) == 1.0
    assert reciprocal_rank(ranked, relevant) == 0.5
def test_missing_relevant_passage_and_zero_k_have_defined_zero_metrics() -> None:
    assert precision_at_k(["P1"], {"P2"}, 3) == 0.0
    assert recall_at_k(["P1"], set(), 3) == 0.0
    assert reciprocal_rank(["P1"], {"P2"}) == 0.0
    assert precision_at_k(["P1"], {"P1"}, 0) == 0.0


@pytest.mark.parametrize("k", [-1, 1.5, True])
def test_metrics_reject_invalid_k(k: int | float | bool) -> None:
    with pytest.raises(ValueError):
        precision_at_k(["P1"], {"P1"}, k)


def test_combined_metric_record_counts_no_hit_queries() -> None:
    metrics = evaluate_ranked_ids(["P2", "P1"], {"P1"}, (1, 3))

    assert metrics["hit"] is True
    assert metrics["first_relevant_rank"] == 2
    assert metrics["metrics"]["precision@1"] == 0.0
    assert metrics["metrics"]["recall@3"] == 1.0
    assert "ndcg@3" not in metrics["metrics"]

    miss = evaluate_ranked_ids(["P2"], {"P1"}, (1, 3))
    assert miss["hit"] is False
    assert miss["first_relevant_rank"] is None

