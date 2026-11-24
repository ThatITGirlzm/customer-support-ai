"""Deterministic from-scratch TF-IDF and BM25 passage retrieval.

The rankers index only a caller-supplied, already materialized retrieval
corpus. They do not load or generate knowledge. Queries and passage text use
the shared ``preprocess_text`` pipeline used by the classifier.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from ml.text_processing import preprocess_text


SENSITIVE_TOPICS = frozenset({"scam_fraud_warning", "human_help_request"})


@dataclass(frozen=True)
class Passage:
    """Eligible passage plus its source traceability metadata."""

    passage_id: str
    topic: str
    text: str
    source_id: str
    source_title: str
    source_url: str
    publication_date: str | None
    accessed_date: str
    section_or_page: str
    status: str
    retrieval_enabled: bool


@dataclass(frozen=True)
class RetrievalResult:
    """Ranked passage reference and original source citation fields."""

    passage_id: str
    source_id: str
    source_title: str
    source_url: str
    publication_date: str | None
    accessed_date: str
    section_or_page: str
    score: float
    rank: int
    method: str


def _required_string(record: Mapping[str, Any], key: str, passage_id: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or (key != "text" and not value.strip()):
        raise ValueError(f"passage {passage_id!r} requires a non-empty {key}")
    return value


def load_corpus(source: str | Path | Sequence[Mapping[str, Any]]) -> list[Passage]:
    """Load and validate eligible retrieval passages from JSON or records.

    This function validates disposition metadata defensively. Callers should
    pass ``data/retrieval_passages.json``; broader approved, review, excluded,
    rejected, or evaluation datasets are not corpus inputs.
    """
    if isinstance(source, (str, Path)):
        with Path(source).open("r", encoding="utf-8") as file:
            records = json.load(file)
    else:
        records = source

    if not isinstance(records, list):
        raise ValueError("retrieval corpus must be a JSON list")

    passages: list[Passage] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"retrieval record at index {index} must be an object")

        raw_id = record.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise ValueError(f"retrieval record at index {index} requires a non-empty id")
        passage_id = raw_id
        if passage_id in seen_ids:
            raise ValueError(f"duplicate passage id {passage_id!r}")
        seen_ids.add(passage_id)

        if record.get("status") != "APPROVED":
            raise ValueError(f"passage {passage_id!r} is not APPROVED")
        if record.get("retrieval_enabled") is not True:
            raise ValueError(f"passage {passage_id!r} is not retrieval_enabled")

        topic = _required_string(record, "topic", passage_id)
        if topic in SENSITIVE_TOPICS:
            raise ValueError(f"sensitive passage {passage_id!r} cannot enter retrieval")

        source_id = _required_string(record, "source_id", passage_id)
        source_title = _required_string(record, "source_title", passage_id)
        source_url = _required_string(record, "source_url", passage_id)
        accessed_date = _required_string(record, "accessed_date", passage_id)
        section_or_page = _required_string(record, "section_or_page", passage_id)
        text = _required_string(record, "text", passage_id)
        publication_date = record.get("publication_date")
        if publication_date is not None and not isinstance(publication_date, str):
            raise ValueError(f"passage {passage_id!r} publication_date must be text or null")

        passages.append(
            Passage(
                passage_id=passage_id,
                topic=topic,
                text=text,
                source_id=source_id,
                source_title=source_title,
                source_url=source_url,
                publication_date=publication_date,
                accessed_date=accessed_date,
                section_or_page=section_or_page,
                status="APPROVED",
                retrieval_enabled=True,
            )
        )

    if not passages:
        raise ValueError("retrieval corpus must contain at least one passage")
    return passages


def _validated_top_k(top_k: int) -> int:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 0:
        raise ValueError("top_k must be a non-negative integer")
    return top_k


class _BaseRetriever:
    """Common immutable passage index data and result formatting."""

    method = "base"

    def __init__(self, passages: Iterable[Passage]) -> None:
        self.passages = tuple(passages)
        if not self.passages:
            raise ValueError("retriever requires at least one passage")
        for passage in self.passages:
            if not isinstance(passage, Passage):
                raise TypeError("retriever inputs must be validated Passage records")
            if passage.status != "APPROVED" or passage.retrieval_enabled is not True:
                raise ValueError("retriever accepts only approved, retrieval-enabled passages")
            if passage.topic in SENSITIVE_TOPICS:
                raise ValueError("sensitive passages cannot enter retrieval")
            for field_name in (
                "passage_id",
                "topic",
                "source_id",
                "source_title",
                "source_url",
                "accessed_date",
                "section_or_page",
            ):
                if not isinstance(getattr(passage, field_name), str) or not getattr(
                    passage, field_name
                ).strip():
                    raise ValueError(f"passage requires a non-empty {field_name}")
            if not isinstance(passage.text, str):
                raise ValueError("passage text must be a string")
            if passage.publication_date is not None and not isinstance(
                passage.publication_date, str
            ):
                raise ValueError("passage publication_date must be text or null")
        ids = [passage.passage_id for passage in self.passages]
        if len(set(ids)) != len(ids):
            raise ValueError("retriever passage IDs must be unique")
        self.tokens = tuple(tuple(preprocess_text(passage.text)) for passage in self.passages)
        self.term_frequencies = tuple(Counter(tokens) for tokens in self.tokens)
        self.document_frequency: Counter[str] = Counter()
        for frequencies in self.term_frequencies:
            self.document_frequency.update(frequencies.keys())

    def search(self, query: str, top_k: int = 3) -> list[RetrievalResult]:
        """Rank eligible passages for *query*; raw scores are not probabilities."""
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        limit = _validated_top_k(top_k)
        if limit == 0:
            return []
        query_tokens = preprocess_text(query)
        if not query_tokens:
            return []
        scores = self._score(query_tokens)
        ranked_indices = sorted(
            (index for index, score in enumerate(scores) if math.isfinite(float(score)) and score > 0.0),
            key=lambda index: (-float(scores[index]), self.passages[index].passage_id),
        )[:limit]
        return [
            self._to_result(self.passages[index], float(scores[index]), rank)
            for rank, index in enumerate(ranked_indices, start=1)
        ]

    def _to_result(self, passage: Passage, score: float, rank: int) -> RetrievalResult:
        return RetrievalResult(
            passage_id=passage.passage_id,
            source_id=passage.source_id,
            source_title=passage.source_title,
            source_url=passage.source_url,
            publication_date=passage.publication_date,
            accessed_date=passage.accessed_date,
            section_or_page=passage.section_or_page,
            score=score,
            rank=rank,
            method=self.method,
        )

    def _score(self, query_tokens: Sequence[str]) -> np.ndarray:
        raise NotImplementedError


class TfidfRetriever(_BaseRetriever):
    """L2-normalized TF-IDF vectors ranked by cosine similarity."""

    method = "tfidf"

    def __init__(self, passages: Iterable[Passage]) -> None:
        super().__init__(passages)
        self.document_count = len(self.passages)
        self.idf = {
            term: math.log((1.0 + self.document_count) / (1.0 + frequency)) + 1.0
            for term, frequency in self.document_frequency.items()
        }
        self.document_vectors = np.zeros(
            (self.document_count, len(self.idf)), dtype=np.float64
        )
        self.term_to_column = {term: column for column, term in enumerate(sorted(self.idf))}
        for row, frequencies in enumerate(self.term_frequencies):
            for term, count in frequencies.items():
                column = self.term_to_column[term]
                self.document_vectors[row, column] = (1.0 + math.log(count)) * self.idf[term]
            norm = float(np.linalg.norm(self.document_vectors[row]))
            if norm > 0.0:
                self.document_vectors[row] /= norm

    def _score(self, query_tokens: Sequence[str]) -> np.ndarray:
        query_frequencies = Counter(query_tokens)
        query_vector = np.zeros(len(self.idf), dtype=np.float64)
        for term, count in query_frequencies.items():
            column = self.term_to_column.get(term)
            if column is not None:
                query_vector[column] = (1.0 + math.log(count)) * self.idf[term]
        norm = float(np.linalg.norm(query_vector))
        if norm == 0.0:
            return np.zeros(self.document_count, dtype=np.float64)
        query_vector /= norm
        return self.document_vectors @ query_vector


class BM25Retriever(_BaseRetriever):
    """BM25 ranker with fixed, documented k1 and b defaults."""

    method = "bm25"

    def __init__(
        self,
        passages: Iterable[Passage],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if isinstance(k1, bool) or not math.isfinite(k1) or k1 <= 0.0:
            raise ValueError("k1 must be a positive finite number")
        if isinstance(b, bool) or not math.isfinite(b) or not 0.0 <= b <= 1.0:
            raise ValueError("b must be a finite number between 0 and 1")
        super().__init__(passages)
        self.k1 = float(k1)
        self.b = float(b)
        self.document_count = len(self.passages)
        self.document_lengths = np.asarray([len(tokens) for tokens in self.tokens], dtype=np.float64)
        self.average_document_length = float(np.mean(self.document_lengths))
        self.idf = {
            term: math.log(
                1.0
                + (self.document_count - frequency + 0.5)
                / (frequency + 0.5)
            )
            for term, frequency in self.document_frequency.items()
        }

    def _score(self, query_tokens: Sequence[str]) -> np.ndarray:
        if self.average_document_length == 0.0:
            return np.zeros(self.document_count, dtype=np.float64)
        scores = np.zeros(self.document_count, dtype=np.float64)
        for term in set(query_tokens):
            term_idf = self.idf.get(term)
            if term_idf is None:
                continue
            for index, frequencies in enumerate(self.term_frequencies):
                term_frequency = frequencies.get(term, 0)
                if term_frequency == 0:
                    continue
                length_norm = 1.0 - self.b + self.b * (
                    self.document_lengths[index] / self.average_document_length
                )
                denominator = term_frequency + self.k1 * length_norm
                scores[index] += term_idf * (
                    term_frequency * (self.k1 + 1.0) / denominator
                )
        return scores

