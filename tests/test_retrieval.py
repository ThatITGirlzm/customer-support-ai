"""Synthetic unit tests for the from-scratch retrieval rankers."""

from __future__ import annotations

from dataclasses import replace
import math

import pytest

from ml.retrieval import BM25Retriever, TfidfRetriever, load_corpus


def _passage(
    passage_id: str,
    text: str,
    *,
    topic: str = "consumer_rights",
    source_id: str = "SRC-TEST",
) -> dict[str, object]:
    return {
        "id": passage_id,
        "topic": topic,
        "text": text,
        "source_id": source_id,
        "source_title": "Synthetic source",
        "source_url": "https://example.invalid/synthetic",
        "publication_date": None,
        "accessed_date": "2026-01-01",
        "section_or_page": "Synthetic section",
        "status": "APPROVED",
        "retrieval_enabled": True,
    }


@pytest.fixture
def synthetic_passages() -> list[dict[str, object]]:
    return [
        _passage("KB-SYN-02", "A bank must treat consumers fairly."),
        _passage("KB-SYN-01", "Consumers have fair treatment rights."),
        _passage("KB-SYN-03", "Fees and complaints are described here."),
    ]


@pytest.mark.parametrize("retriever_type", [TfidfRetriever, BM25Retriever])
def test_both_rankers_return_source_traceable_deterministic_results(
    retriever_type: type[TfidfRetriever] | type[BM25Retriever],
    synthetic_passages: list[dict[str, object]],
) -> None:
    corpus = load_corpus(synthetic_passages)
    retriever = retriever_type(corpus)

    results = retriever.search("consumer fair treatment", top_k=2)

    assert len(results) == 2
    assert results[0].passage_id in {"KB-SYN-01", "KB-SYN-02"}
    assert results == retriever.search("consumer fair treatment", top_k=2)
    assert [result.rank for result in results] == [1, 2]
    assert all(result.score > 0 for result in results)
    assert all(result.method == retriever.method for result in results)
    assert all(result.source_id == "SRC-TEST" for result in results)
    assert all(result.source_url == "https://example.invalid/synthetic" for result in results)


def test_tfidf_cosine_scores_are_normalized_and_bounded(
    synthetic_passages: list[dict[str, object]],
) -> None:
    retriever = TfidfRetriever(load_corpus(synthetic_passages))
    results = retriever.search("Consumers have fair treatment rights")

    assert results
    assert all(0.0 < result.score <= 1.0 + 1e-12 for result in results)
    assert math.isclose(results[0].score, 1.0, rel_tol=1e-12)


def test_tfidf_idf_vectors_and_cosine_match_documented_formula() -> None:
    corpus = load_corpus(
        [_passage("KB-A", "alpha beta"), _passage("KB-B", "alpha alpha")]
    )
    retriever = TfidfRetriever(corpus)
    beta_idf = math.log(3.0 / 2.0) + 1.0
    expected_first_score = 1.0 / math.sqrt(1.0 + beta_idf**2)

    assert retriever.document_frequency["alpha"] == 2
    assert retriever.document_frequency["beta"] == 1
    assert retriever.idf["alpha"] == pytest.approx(1.0)
    assert retriever.idf["beta"] == pytest.approx(beta_idf)
    results = retriever.search("alpha", top_k=2)
    assert [result.passage_id for result in results] == ["KB-B", "KB-A"]
    assert results[0].score == pytest.approx(1.0)
    assert results[1].score == pytest.approx(expected_first_score)


@pytest.mark.parametrize("retriever_type", [TfidfRetriever, BM25Retriever])
def test_empty_unmatched_and_oov_queries_return_no_results(
    retriever_type: type[TfidfRetriever] | type[BM25Retriever],
    synthetic_passages: list[dict[str, object]],
) -> None:
    retriever = retriever_type(load_corpus(synthetic_passages))

    assert retriever.search("") == []
    assert retriever.search("qzxvblorf") == []
    assert retriever.search("!!! 12345") == []


@pytest.mark.parametrize("retriever_type", [TfidfRetriever, BM25Retriever])
def test_top_k_and_query_type_are_validated(
    retriever_type: type[TfidfRetriever] | type[BM25Retriever],
    synthetic_passages: list[dict[str, object]],
) -> None:
    retriever = retriever_type(load_corpus(synthetic_passages))

    assert retriever.search("consumer", top_k=0) == []
    with pytest.raises(ValueError):
        retriever.search("consumer", top_k=-1)
    with pytest.raises(TypeError):
        retriever.search(123)  # type: ignore[arg-type]


def test_empty_document_is_ignored_and_empty_corpus_is_rejected() -> None:
    corpus = load_corpus([_passage("KB-EMPTY", "")])
    assert TfidfRetriever(corpus).search("anything") == []
    assert BM25Retriever(corpus).search("anything") == []

    with pytest.raises(ValueError, match="at least one"):
        TfidfRetriever([])


def test_bm25_document_frequency_lengths_and_score_match_formula() -> None:
    corpus = load_corpus(
        [_passage("KB-A", "alpha beta"), _passage("KB-B", "alpha alpha")]
    )
    retriever = BM25Retriever(corpus)
    expected_idf = math.log(1.0 + 0.5 / 2.5)
    expected_second_score = expected_idf * (2.0 * 2.5) / (2.0 + 1.5)

    assert retriever.document_frequency["alpha"] == 2
    assert retriever.document_frequency["beta"] == 1
    assert retriever.document_lengths.tolist() == [2.0, 2.0]
    assert retriever.average_document_length == 2.0
    assert retriever.idf["alpha"] == pytest.approx(expected_idf)
    results = retriever.search("alpha", top_k=2)
    assert [result.passage_id for result in results] == ["KB-B", "KB-A"]
    assert results[0].score == pytest.approx(expected_second_score)


@pytest.mark.parametrize("retriever_type", [TfidfRetriever, BM25Retriever])
def test_equal_scores_break_ties_by_passage_id(
    retriever_type: type[TfidfRetriever] | type[BM25Retriever],
) -> None:
    corpus = load_corpus(
        [_passage("KB-Z", "alpha beta"), _passage("KB-A", "alpha beta")]
    )
    results = retriever_type(corpus).search("alpha beta", top_k=2)

    assert [result.passage_id for result in results] == ["KB-A", "KB-Z"]
    assert results[0].score == pytest.approx(results[1].score)


def test_loader_rejects_duplicate_ids_invalid_dispositions_and_sensitive_topics() -> None:
    duplicated = [_passage("KB-DUP", "first"), _passage("KB-DUP", "second")]
    with pytest.raises(ValueError, match="duplicate"):
        load_corpus(duplicated)

    disabled = _passage("KB-DISABLED", "text")
    disabled["retrieval_enabled"] = False
    with pytest.raises(ValueError, match="retrieval_enabled"):
        load_corpus([disabled])

    unapproved = _passage("KB-REVIEW", "text")
    unapproved["status"] = "NEEDS_REVIEW"
    with pytest.raises(ValueError, match="APPROVED"):
        load_corpus([unapproved])

    sensitive = _passage("KB-SENSITIVE", "text", topic="scam_fraud_warning")
    with pytest.raises(ValueError, match="sensitive"):
        load_corpus([sensitive])


def test_loader_rejects_missing_traceability_fields() -> None:
    invalid = _passage("KB-MISSING", "text")
    del invalid["source_url"]

    with pytest.raises(ValueError, match="source_url"):
        load_corpus([invalid])


def test_retriever_rechecks_eligibility_of_passage_objects(
    synthetic_passages: list[dict[str, object]],
) -> None:
    passage = load_corpus(synthetic_passages)[0]

    with pytest.raises(ValueError, match="sensitive"):
        TfidfRetriever([replace(passage, topic="human_help_request")])
    with pytest.raises(ValueError, match="approved"):
        BM25Retriever([replace(passage, retrieval_enabled=False)])


@pytest.mark.parametrize("retriever_type", [TfidfRetriever, BM25Retriever])
@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("accessed_date", ""),
        ("accessed_date", None),
        ("section_or_page", ""),
        ("section_or_page", None),
        ("publication_date", 2026),
    ],
)
def test_retriever_rejects_missing_source_metadata_on_direct_passages(
    retriever_type: type[TfidfRetriever] | type[BM25Retriever],
    field_name: str,
    value: object,
    synthetic_passages: list[dict[str, object]],
) -> None:
    passage = load_corpus(synthetic_passages)[0]
    invalid_passage = replace(passage, **{field_name: value})

    with pytest.raises(ValueError, match=field_name):
        retriever_type([invalid_passage])


@pytest.mark.parametrize(
    ("k1", "b"),
    [(0.0, 0.75), (-1.0, 0.75), (1.5, -0.1), (1.5, 1.1)],
)
def test_bm25_rejects_invalid_parameters(
    k1: float, b: float, synthetic_passages: list[dict[str, object]]
) -> None:
    with pytest.raises(ValueError):
        BM25Retriever(load_corpus(synthetic_passages), k1=k1, b=b)


