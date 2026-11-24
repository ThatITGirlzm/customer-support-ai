from __future__ import annotations

from app.schemas import ProcessRequest
from app.service import ApplicationService
from ml.retrieval import RetrievalResult


class _Classifier:
    def __init__(self, result: str | None = "complaints_process") -> None:
        self.result = result
        self.calls = 0

    def predict_intent(self, question: str) -> str | None:
        self.calls += 1
        return self.result


class _Retriever:
    def __init__(self, results=None, fail: bool = False) -> None:
        self.results = list(results or [])
        self.fail = fail
        self.calls = 0

    def search(self, query: str, top_k: int = 3):
        self.calls += 1
        if self.fail:
            raise RuntimeError("synthetic retrieval error")
        return self.results


def _high_score_result() -> RetrievalResult:
    return RetrievalResult(
        passage_id="KB-SYN-1",
        source_id="SRC-SYN-1",
        source_title="Synthetic source",
        source_url="https://example.invalid/synthetic",
        publication_date=None,
        accessed_date="2026-01-01",
        section_or_page="Synthetic fixture",
        score=999999.0,
        rank=1,
        method="tfidf",
    )


def test_high_retrieval_score_cannot_authorize_answer_without_catalog() -> None:
    classifier = _Classifier()
    retriever = _Retriever([_high_score_result()])
    result = ApplicationService(classifier, retriever).process(
        ProcessRequest(question="What does the approved source say about a complaint?")
    )

    assert result.action == "ABSTAIN_NOT_IN_SOURCES"
    assert result.reason_code == "NO_APPROVED_ANSWER_RULE"
    assert result.citations == []
    assert "999999" not in result.model_dump_json()
    assert classifier.calls == 1
    assert retriever.calls == 1


def test_unknown_or_zero_evidence_intent_stops_before_retrieval() -> None:
    classifier = _Classifier(result=None)
    retriever = _Retriever([_high_score_result()])
    result = ApplicationService(classifier, retriever).process(
        ProcessRequest(question="unseen synthetic words")
    )

    assert result.action == "ABSTAIN_NOT_IN_SOURCES"
    assert result.reason_code == "UNKNOWN_INTENT"
    assert retriever.calls == 0


def test_retriever_failure_returns_sanitized_unavailable_response() -> None:
    classifier = _Classifier()
    retriever = _Retriever(fail=True)
    secret_like_input = "synthetic details with account 123456"
    result = ApplicationService(classifier, retriever).process(
        ProcessRequest(question=secret_like_input)
    )

    assert result.action == "SERVICE_UNAVAILABLE"
    assert result.reason_code == "RETRIEVER_UNAVAILABLE"
    assert secret_like_input not in result.model_dump_json()


def test_question_limit_is_configurable_and_provisional() -> None:
    service = ApplicationService(_Classifier(), _Retriever(), max_question_codepoints=20)
    result = service.process(ProcessRequest(question="x" * 21))
    assert result.action == "INVALID_REQUEST"
    assert result.reason_code == "QUESTION_TOO_LONG"


def test_quoted_sensitive_example_is_not_routed_by_classifier_alone() -> None:
    classifier = _Classifier(result="scam_fraud_warning")
    retriever = _Retriever([_high_score_result()])
    result = ApplicationService(classifier, retriever).process(
        ProcessRequest(
            question="In the training notes, the quoted example was 'I was scammed.'"
        )
    )

    assert result.action == "ABSTAIN_NOT_IN_SOURCES"
    assert result.reason_code == "SENSITIVE_INTENT_POLICY_PENDING"
    assert retriever.calls == 0
