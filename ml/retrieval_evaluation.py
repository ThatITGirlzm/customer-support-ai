"""Binary-relevance metrics and validation-only retrieval evaluation helpers."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from ml.retrieval import BM25Retriever, Passage, RetrievalResult, TfidfRetriever
from ml.text_processing import preprocess_text


def _validate_k(k: int) -> int:
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        raise ValueError("k must be a non-negative integer")
    return k


def precision_at_k(ranked_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    """Precision@k with a fixed denominator of k, including missing slots."""
    limit = _validate_k(k)
    if limit == 0:
        return 0.0
    return sum(identifier in relevant_ids for identifier in ranked_ids[:limit]) / limit


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    """Recall@k; queries with no relevance annotations are assigned zero."""
    limit = _validate_k(k)
    if not relevant_ids:
        return 0.0
    return sum(identifier in relevant_ids for identifier in ranked_ids[:limit]) / len(relevant_ids)


def reciprocal_rank(ranked_ids: Sequence[str], relevant_ids: set[str]) -> float:
    """Reciprocal rank of the first relevant passage, or zero for a miss."""
    for rank, identifier in enumerate(ranked_ids, start=1):
        if identifier in relevant_ids:
            return 1.0 / rank
    return 0.0


def evaluate_ranked_ids(
    ranked_ids: Sequence[str], relevant_ids: set[str], ks: Iterable[int] = (1, 3)
) -> dict[str, Any]:
    """Calculate query-level binary retrieval metrics and hit diagnostics."""
    valid_ks = tuple(_validate_k(k) for k in ks)
    first_relevant_rank = next(
        (rank for rank, identifier in enumerate(ranked_ids, start=1) if identifier in relevant_ids),
        None,
    )
    metrics: dict[str, float] = {}
    for k in valid_ks:
        metrics[f"precision@{k}"] = precision_at_k(ranked_ids, relevant_ids, k)
        metrics[f"recall@{k}"] = recall_at_k(ranked_ids, relevant_ids, k)
    metrics["mrr"] = reciprocal_rank(ranked_ids, relevant_ids)
    return {
        "hit": first_relevant_rank is not None,
        "first_relevant_rank": first_relevant_rank,
        "metrics": metrics,
    }


def evaluate_records(
    passages: Sequence[Passage],
    records: Sequence[Mapping[str, Any]],
    ks: Iterable[int] = (1, 3),
) -> dict[str, Any]:
    """Evaluate TF-IDF and BM25 on the supplied answerable records.

    This function does not load datasets. The validation-only script owns the
    pinned input path and schema checks; tests call this with synthetic rows.
    """
    valid_ks = tuple(_validate_k(k) for k in ks)
    retrievers = (TfidfRetriever(passages), BM25Retriever(passages))
    if not records:
        raise ValueError("evaluation requires at least one annotated record")
    identifiers: set[str] = set()
    passages_by_id = {passage.passage_id: passage for passage in passages}
    corpus_tokens = {
        token for passage in passages for token in preprocess_text(passage.text)
    }
    per_method: dict[str, list[dict[str, Any]]] = {retriever.method: [] for retriever in retrievers}

    for record in records:
        example_id = record.get("example_id")
        question = record.get("question")
        relevant = record.get("supporting_passage_ids")
        if not isinstance(example_id, str) or not example_id.strip():
            raise ValueError("each evaluation record requires example_id")
        if example_id in identifiers:
            raise ValueError(f"duplicate evaluation example_id {example_id!r}")
        identifiers.add(example_id)
        if not isinstance(question, str):
            raise ValueError(f"evaluation record {example_id!r} requires question text")
        if not isinstance(relevant, list) or not relevant or not all(
            isinstance(identifier, str) for identifier in relevant
        ):
            raise ValueError(f"evaluation record {example_id!r} requires supporting passage IDs")
        relevant_ids = set(relevant)
        unknown = relevant_ids - passages_by_id.keys()
        if unknown:
            raise ValueError(f"evaluation record {example_id!r} references unknown passages: {sorted(unknown)}")

        query_tokens = set(preprocess_text(question))
        relevant_tokens = set(
            token
            for passage_id in relevant_ids
            for token in preprocess_text(passages_by_id[passage_id].text)
        )
        for retriever in retrievers:
            results: list[RetrievalResult] = retriever.search(
                question, top_k=max(valid_ks, default=3)
            )
            ranked_ids = [result.passage_id for result in results]
            metric_record = evaluate_ranked_ids(ranked_ids, relevant_ids, valid_ks)
            per_method[retriever.method].append(
                {
                    "example_id": example_id,
                    "relevant_passage_ids": sorted(relevant_ids),
                    "ranked": [
                        {"passage_id": result.passage_id, "source_id": result.source_id,
                         "score": result.score, "rank": result.rank}
                        for result in results
                    ],
                    "query_unique_token_count": len(query_tokens),
                    "query_relevant_passage_token_overlap": sorted(query_tokens & relevant_tokens),
                    "query_corpus_token_overlap": sorted(query_tokens & corpus_tokens),
                    **metric_record,
                }
            )

    summaries: dict[str, Any] = {}
    for method, rows in per_method.items():
        metric_names = sorted(rows[0]["metrics"])
        summaries[method] = {
            "query_count": len(rows),
            "hits": sum(bool(row["hit"]) for row in rows),
            "misses": sum(not bool(row["hit"]) for row in rows),
            "no_overlap_queries": sum(
                row["query_unique_token_count"] == 0
                or not row["query_corpus_token_overlap"]
                for row in rows
            ),
            "macro_metrics": {
                name: sum(row["metrics"][name] for row in rows) / len(rows)
                for name in metric_names
            },
        }
    return {"summaries": summaries, "per_method": per_method}

