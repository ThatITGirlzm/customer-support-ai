from __future__ import annotations

import pytest

from app.schemas import ProcessRequest
from app.service import ApplicationService
from ml.retrieval import Passage, RetrievalResult


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


def _passage(passage_id: str, topic: str, text: str) -> Passage:
    return Passage(
        passage_id=passage_id,
        topic=topic,
        text=text,
        source_id="SRC-SYN-1",
        source_title="Synthetic approved source",
        source_url="https://example.invalid/approved",
        publication_date="2026-01",
        accessed_date="2026-01-01",
        section_or_page="Synthetic section",
        status="APPROVED",
        retrieval_enabled=True,
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


@pytest.mark.parametrize("question", ["hello", "what's your name?"])
def test_smalltalk_uses_existing_out_of_scope_response_without_retrieval(
    question: str,
) -> None:
    classifier = _Classifier(result="out_of_scope")
    retriever = _Retriever([_high_score_result()])
    result = ApplicationService(classifier, retriever).process(
        ProcessRequest(question=question)
    )

    assert result.action == "DECLINE_OUT_OF_SCOPE"
    assert result.intent is None
    assert "Averse" in result.response_text
    assert retriever.calls == 0


def test_stolen_card_is_referred_before_classifier_or_retrieval() -> None:
    classifier = _Classifier()
    retriever = _Retriever([_high_score_result()])
    result = ApplicationService(classifier, retriever).process(
        ProcessRequest(question="Someone has stolen my bank card.")
    )

    assert result.action == "REFER_HUMAN"
    assert result.referral_state == "NOT_SENT"
    assert classifier.calls == 0
    assert retriever.calls == 0


def test_boZ_complaint_sequence_returns_only_mapped_passages_and_citations() -> None:
    passages = [
        _passage("KB001", "complaints_process", "First approved complaint step."),
        _passage("KB002", "complaints_process", "Second approved complaint step."),
        _passage("KB003", "complaints_process", "Third approved complaint step."),
    ]
    retriever = _Retriever([_high_score_result()])
    service = ApplicationService(
        _Classifier("complaints_process"), retriever, approved_passages=passages
    )

    result = service.process(
        ProcessRequest(question="How do I file a complaint with the Bank of Zambia?")
    )

    assert result.action == "ANSWER_FROM_SOURCE"
    assert "First approved complaint step." in result.response_text
    assert "Third approved complaint step." in result.response_text
    assert [citation.passage_id for citation in result.citations] == ["KB001", "KB002", "KB003"]
    assert "direct BoZ filing form or contact details" in result.response_text


def test_license_directory_question_returns_cited_active_passage() -> None:
    passage = _passage(
        "KB016",
        "licensed_institutions",
        "Consult BoZ's live directory and check the listed category.",
    )
    service = ApplicationService(
        _Classifier("licensed_institutions"),
        _Retriever([_high_score_result()]),
        approved_passages=[passage],
    )

    result = service.process(
        ProcessRequest(
            question="How do I check if a financial institution is licensed?"
        )
    )

    assert result.action == "ANSWER_FROM_SOURCE"
    assert result.response_text == passage.text
    assert [citation.passage_id for citation in result.citations] == ["KB016"]


def test_consumer_protection_mandate_answer_is_limited_and_cited() -> None:
    passages = [
        _passage("KB008", "consumer_rights", "Providers should operate fairly."),
        _passage("KB025", "consumer_rights", "Dispute resolution is a strategic priority."),
    ]
    service = ApplicationService(
        _Classifier("consumer_rights"),
        _Retriever([_high_score_result()]),
        approved_passages=passages,
    )

    result = service.process(
        ProcessRequest(question="What is the BoZ consumer protection mandate?")
    )

    assert result.action == "ANSWER_FROM_SOURCE"
    assert [citation.passage_id for citation in result.citations] == ["KB008", "KB025"]
    assert "not a complete statement" in result.response_text


def test_comprehensive_customer_rights_question_abstains_when_catalog_has_no_answer() -> None:
    service = ApplicationService(_Classifier("consumer_rights"), _Retriever([]))

    result = service.process(
        ProcessRequest(question="What are my rights as a bank customer?")
    )

    assert result.action == "ABSTAIN_NOT_IN_SOURCES"
    assert "does not contain a reviewed answer" in result.response_text


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
