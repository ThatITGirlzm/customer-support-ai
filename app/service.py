"""Application orchestration for safety, candidate retrieval, and demo recording."""

from __future__ import annotations

import csv
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence

from ml.inference import FIXED_INTENTS, NaiveBayesInference
from ml.retrieval import BM25Retriever, Passage, RetrievalResult, TfidfRetriever, load_corpus

from app.config import Settings
from app.demo_outbox import DemoOutboxUnavailable, LocalDemoOutbox
from app.safety import SafetyDecision, SafetyOutcome, SafetyPreflight
from app.schemas import (
    Citation,
    DemoComplaintRequest,
    DemonstrationStatus,
    ProcessRequest,
    ProcessResponse,
)


_LOG = logging.getLogger("averse.application")
_SENSITIVE_INTENTS = frozenset({"scam_fraud_warning", "human_help_request"})

_GREETING_PATTERNS = (
    re.compile(r"^(?:hi|hello|hey)(?: there)?[.!?]*$", re.IGNORECASE),
    re.compile(r"^(?:good morning|good afternoon|good evening)[.!?]*$", re.IGNORECASE),
    re.compile(r"^how are you(?: doing)?[.!?]*$", re.IGNORECASE),
)
_NAME_QUESTION_PATTERNS = (
    re.compile(r"^what(?:'s| is) your name[.!?]*$", re.IGNORECASE),
    re.compile(r"^who are you[.!?]*$", re.IGNORECASE),
    re.compile(r"^what are you called[.!?]*$", re.IGNORECASE),
)
_COMPLAINT_WITH_BOZ = re.compile(
    r"^(?:how do i|how can i|where do i)\s+(?:file|lodge|make|submit)\s+"
    r"(?:a\s+)?complaints?\s+(?:with|to)\s+(?:the\s+)?(?:bank of zambia|boz)[.!?]*$",
    re.IGNORECASE,
)
_LICENSE_DIRECTORY_QUESTION = re.compile(
    r"^(?:how do i|how can i|where can i)\s+(?:check|verify|find out)\s+"
    r"if\s+(?:a\s+)?financial institution\s+is\s+(?:licensed|licenced)[.!?]*$",
    re.IGNORECASE,
)
_BOZ_CONSUMER_MANDATE_QUESTION = re.compile(
    r"^(?:what is|what are)\s+(?:the\s+)?(?:boz|bank of zambia)\s+"
    r"consumer protection\s+(?:mandate|role|responsibilities)[.!?]*$",
    re.IGNORECASE,
)


class IntentClassifier(Protocol):
    def predict_intent(self, question: str) -> str | None: ...


class Retriever(Protocol):
    def search(self, query: str, top_k: int = 3) -> Sequence[RetrievalResult]: ...


class DemoOutbox(Protocol):
    def record_and_queue(self, complaint_id: str, complaint_details: str): ...


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_title: str
    source_url: str


def load_source_register(path: Path) -> dict[str, SourceRecord]:
    """Load citation joins from the approved source register only."""
    required = {"source_id", "source_title", "official_url"}
    records: dict[str, SourceRecord] = {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source_file:
            reader = csv.DictReader(source_file)
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise ValueError("source register is missing required citation columns")
            for row in reader:
                source_id = (row.get("source_id") or "").strip()
                title = (row.get("source_title") or "").strip()
                url = (row.get("official_url") or "").strip()
                if not source_id or not title or not url or source_id in records:
                    raise ValueError("source register has missing or duplicate citation metadata")
                records[source_id] = SourceRecord(source_id, title, url)
    except OSError as exc:
        raise ValueError("approved source register could not be loaded") from exc
    return records


def validate_source_joins(
    passages: Sequence[Passage], sources: Mapping[str, SourceRecord]
) -> None:
    for passage in passages:
        source = sources.get(passage.source_id)
        if source is None:
            raise ValueError("active passage has no source-register record")
        if source.source_title != passage.source_title or source.source_url != passage.source_url:
            raise ValueError("active passage citation does not match the source register")


class ApplicationService:
    """A deterministic service with no answer rules enabled by default."""

    def __init__(
        self,
        classifier: IntentClassifier,
        retriever: Retriever,
        *,
        safety: SafetyPreflight | None = None,
        max_question_codepoints: int = 2000,
        demo_enabled: bool = False,
        demo_recipient_phone: str | None = None,
        demo_outbox: DemoOutbox | None = None,
        approved_passages: Sequence[Passage] = (),
    ) -> None:
        if max_question_codepoints < 1:
            raise ValueError("max_question_codepoints must be positive")
        self.classifier = classifier
        self.retriever = retriever
        self.safety = safety or SafetyPreflight()
        self.max_question_codepoints = max_question_codepoints
        self.demo_enabled = demo_enabled
        self._demo_recipient_phone = demo_recipient_phone
        self.demo_outbox = demo_outbox
        self.approved_passages = {passage.passage_id: passage for passage in approved_passages}

    @staticmethod
    def _request_id() -> str:
        return "REQ-" + uuid.uuid4().hex

    @staticmethod
    def _invalid(request_id: str, reason: str) -> ProcessResponse:
        return ProcessResponse(
            request_id=request_id,
            action="INVALID_REQUEST",
            response_text="The request is invalid. Check the question and try again.",
            reason_code=reason,
        )

    def _unavailable(self, request_id: str, reason: str) -> ProcessResponse:
        return ProcessResponse(
            request_id=request_id,
            action="SERVICE_UNAVAILABLE",
            response_text="Averse is temporarily unable to process this request safely.",
            reason_code=reason,
        )

    def _preflight(self, request_id: str, question: str) -> SafetyDecision | ProcessResponse:
        try:
            return self.safety.evaluate(question)
        except Exception:
            _LOG.error("safety preflight failed request_id=%s", request_id)
            return self._unavailable(request_id, "SAFETY_PREFLIGHT_UNAVAILABLE")

    def _safety_response(
        self, request_id: str, decision: SafetyDecision
    ) -> ProcessResponse | None:
        if decision.outcome is SafetyOutcome.BLOCK_INJECTION:
            return ProcessResponse(
                request_id=request_id,
                action="BLOCK_INJECTION",
                response_text="This request cannot be processed because it asks the service to bypass its safety or source rules.",
                reason_code=decision.reason_code,
            )
        if decision.outcome is SafetyOutcome.REFER_HUMAN:
            return ProcessResponse(
                request_id=request_id,
                action="REFER_HUMAN",
                response_text=(
                    "This request needs human assistance. It has not been sent to a bank or "
                    "the Bank of Zambia, and no official complaint reference was created."
                ),
                reason_code="REFERRAL_CHANNEL_NOT_CONFIGURED",
                referral_state="NOT_SENT",
            )
        if decision.outcome is SafetyOutcome.CLARIFICATION_REQUIRED:
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text=(
                    "I cannot tell whether this concerns an active sensitive situation. "
                    "Please clarify. No referral was sent."
                ),
                reason_code=decision.reason_code,
                referral_state="NOT_SENT",
            )
        return None

    def _validate_request(self, request_id: str, request: ProcessRequest) -> str | ProcessResponse:
        if not isinstance(request, ProcessRequest):
            return self._invalid(request_id, "INVALID_REQUEST_SCHEMA")
        question = request.question
        if not question.strip():
            return self._invalid(request_id, "EMPTY_QUESTION")
        if len(question) > self.max_question_codepoints:
            return self._invalid(request_id, "QUESTION_TOO_LONG")
        return question

    @staticmethod
    def _smalltalk_response(request_id: str, question: str) -> ProcessResponse | None:
        normalized = question.strip()
        if any(pattern.fullmatch(normalized) for pattern in _GREETING_PATTERNS):
            return ProcessResponse(
                request_id=request_id,
                action="DECLINE_OUT_OF_SCOPE",
                response_text=(
                    "Hello, I'm Averse, a banking consumer-information assistant for Zambia. "
                    "I can help with general questions supported by approved Bank of Zambia "
                    "passages, but I can’t access accounts or carry out transactions. "
                    "How may I help you?"
                ),
                intent=None,
                reason_code="GREETING",
            )
        if any(pattern.fullmatch(normalized) for pattern in _NAME_QUESTION_PATTERNS):
            return ProcessResponse(
                request_id=request_id,
                action="DECLINE_OUT_OF_SCOPE",
                response_text=(
                    "Hello, I'm Averse, a banking consumer-information assistant for Zambia."
                ),
                intent=None,
                reason_code="ASSISTANT_IDENTITY",
            )
        return None

    def process(self, request: ProcessRequest) -> ProcessResponse:
        request_id = self._request_id()
        question_or_error = self._validate_request(request_id, request)
        if isinstance(question_or_error, ProcessResponse):
            return question_or_error
        question = question_or_error

        decision_or_error = self._preflight(request_id, question)
        if isinstance(decision_or_error, ProcessResponse):
            return decision_or_error
        safety_response = self._safety_response(request_id, decision_or_error)
        if safety_response is not None:
            return safety_response

        try:
            intent = self.classifier.predict_intent(question)
        except Exception:
            _LOG.error("intent classification failed request_id=%s", request_id)
            return self._unavailable(request_id, "CLASSIFIER_UNAVAILABLE")

        if intent is not None and intent not in FIXED_INTENTS:
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text="I could not determine a supported answer from the approved sources.",
                reason_code="UNKNOWN_INTENT",
            )
        if intent is None:
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text="I could not determine a supported answer from the approved sources.",
                reason_code="UNKNOWN_INTENT",
            )

        if intent == "out_of_scope":
            smalltalk_response = self._smalltalk_response(request_id, question)
            if smalltalk_response is not None:
                return smalltalk_response
            return ProcessResponse(
                request_id=request_id,
                action="DECLINE_OUT_OF_SCOPE",
                response_text=(
                    "I’m Averse, a banking consumer-information assistant for Zambia. "
                    "I can help with general questions supported by approved Bank of Zambia "
                    "passages, but I can’t access accounts or carry out transactions."
                ),
                intent=intent,
                reason_code="OUT_OF_SCOPE",
            )

        # Classifier authority for user-facing routing remains pending. A
        # sensitive candidate must not cause retrieval or an unapproved
        # referral; return a safe abstention instead.
        if intent in _SENSITIVE_INTENTS:
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text=(
                    "The request could not be handled under the approved "
                    "answer and referral rules. No referral was sent."
                ),
                reason_code="SENSITIVE_INTENT_POLICY_PENDING",
                referral_state="NOT_SENT",
            )

        try:
            results = self.retriever.search(question, top_k=3)
        except Exception:
            _LOG.error("retrieval failed request_id=%s", request_id)
            return self._unavailable(request_id, "RETRIEVER_UNAVAILABLE")

        return self._evidence_response(request_id, intent, question, results)

    def _evidence_response(
        self,
        request_id: str,
        intent: str,
        question: str,
        results: Sequence[RetrievalResult],
    ) -> ProcessResponse:
        # Only narrow question forms with a direct active-passage mapping may
        # produce answers. Retrieval rankings alone never authorize a response.
        if (
            intent == "complaints_process"
            and _COMPLAINT_WITH_BOZ.fullmatch(question.strip())
        ):
            passage_ids = ("KB001", "KB002", "KB003")
            limitation = (
                "These passages describe the escalation sequence; they do not specify "
                "a direct BoZ filing form or contact details."
            )
        elif (
            intent == "licensed_institutions"
            and _LICENSE_DIRECTORY_QUESTION.fullmatch(question.strip())
        ):
            passage_ids = ("KB016",)
            limitation = None
        elif (
            intent == "consumer_rights"
            and _BOZ_CONSUMER_MANDATE_QUESTION.fullmatch(question.strip())
        ):
            passage_ids = ("KB008", "KB025")
            limitation = (
                "These passages describe consumer-protection priorities, not a complete "
                "statement of the Bank of Zambia's legal mandate."
            )
        else:
            reason = "NO_APPROVED_ANSWER_RULE" if results else "NO_SUPPORTING_PASSAGE"
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text="The approved passage dataset does not contain a reviewed answer for this request.",
                intent=intent,
                reason_code=reason,
            )

        mapped_passages = [self.approved_passages.get(passage_id) for passage_id in passage_ids]
        if any(passage is None for passage in mapped_passages):
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text="The approved passage dataset does not contain a reviewed answer for this request.",
                intent=intent,
                reason_code="ANSWER_PASSAGE_UNAVAILABLE",
            )

        passages = [passage for passage in mapped_passages if passage is not None]
        response_text = "\n\n".join(passage.text for passage in passages)
        if limitation:
            response_text += "\n\n" + limitation
        citations = [
            Citation(
                passage_id=passage.passage_id,
                source_id=passage.source_id,
                source_title=passage.source_title,
                source_url=passage.source_url,
                publication_date=passage.publication_date,
                accessed_date=passage.accessed_date,
                section_or_page=passage.section_or_page,
            )
            for passage in passages
        ]
        return ProcessResponse(
            request_id=request_id,
            action="ANSWER_FROM_SOURCE",
            response_text=response_text,
            intent=intent,
            citations=citations,
            reason_code="APPROVED_PASSAGE_RULE",
        )

    def process_demo_complaint(self, request: DemoComplaintRequest) -> ProcessResponse:
        request_id = self._request_id()
        if not isinstance(request, DemoComplaintRequest):
            return self._invalid(request_id, "INVALID_DEMO_REQUEST_SCHEMA")
        question_or_error = self._validate_request(request_id, request)
        if isinstance(question_or_error, ProcessResponse):
            return question_or_error
        question = question_or_error

        if not self.demo_enabled:
            return self._unavailable(request_id, "DEMO_MODE_DISABLED")
        if not self._demo_recipient_phone or self.demo_outbox is None:
            return self._unavailable(request_id, "DEMO_RECIPIENT_OR_OUTBOX_NOT_CONFIGURED")

        decision_or_error = self._preflight(request_id, question)
        if isinstance(decision_or_error, ProcessResponse):
            return decision_or_error
        decision = decision_or_error
        if decision.outcome is not SafetyOutcome.REFER_HUMAN:
            response = self._safety_response(request_id, decision)
            if response is not None:
                return response
            return ProcessResponse(
                request_id=request_id,
                action="ABSTAIN_NOT_IN_SOURCES",
                response_text=(
                    "The demonstration workflow records only requests that the safety "
                    "preflight routes to human assistance."
                ),
                reason_code="NOT_ELIGIBLE_FOR_DEMO_REFERRAL",
            )

        complaint_id = "DEMO-" + uuid.uuid4().hex
        try:
            receipt = self.demo_outbox.record_and_queue(complaint_id, question)
        except (DemoOutboxUnavailable, OSError, ValueError):
            _LOG.error("demo notification could not be queued request_id=%s", request_id)
            return ProcessResponse(
                request_id=request_id,
                action="SERVICE_UNAVAILABLE",
                response_text=(
                    "The demonstration request could not be recorded locally. "
                    "No notification was sent and no referral was submitted."
                ),
                reason_code="DEMO_OUTBOX_UNAVAILABLE",
                referral_state="NOT_SENT",
                demonstration=DemonstrationStatus(
                    complaint_id=None,
                    record_state="NOT_RECORDED",
                    notification_state="NOT_QUEUED",
                ),
            )
        except Exception:
            _LOG.error("unexpected demo outbox error request_id=%s", request_id)
            return ProcessResponse(
                request_id=request_id,
                action="SERVICE_UNAVAILABLE",
                response_text=(
                    "The demonstration request could not be recorded locally. "
                    "No notification was sent and no referral was submitted."
                ),
                reason_code="DEMO_OUTBOX_UNAVAILABLE",
                referral_state="NOT_SENT",
                demonstration=DemonstrationStatus(
                    complaint_id=None,
                    record_state="NOT_RECORDED",
                    notification_state="NOT_QUEUED",
                ),
            )

        return ProcessResponse(
            request_id=request_id,
            action="REFER_HUMAN",
            response_text=(
                "Your request has been recorded by the Averse demonstration system. "
                f"Your local Averse demonstration complaint ID is {receipt.complaint_id}. "
                "A notification was queued locally only; it was not sent to a phone. "
                "This has not been submitted to a bank or the Bank of Zambia."
            ),
            reason_code="DEMONSTRATION_ONLY",
            referral_state="NOT_SENT",
            demonstration=DemonstrationStatus(
                complaint_id=receipt.complaint_id,
                record_state="RECORDED_LOCAL_ONLY",
                notification_state=receipt.notification_state,
                notification_delivered=False,
                external_referral_submitted=False,
            ),
        )


def build_default_service(settings: Settings) -> ApplicationService:
    """Build from the canonical approved corpus and frozen NB artifact only."""
    corpus_path = settings.project_root / "data" / "retrieval_passages.json"
    source_path = settings.project_root / "data" / "sources_register_final.csv"
    model_path = (
        settings.project_root
        / "data"
        / "models"
        / "day4-text-processing-v2"
        / "intent_models.json"
    )
    passages = load_corpus(corpus_path)
    source_register = load_source_register(source_path)
    validate_source_joins(passages, source_register)

    classifier = NaiveBayesInference.load(model_path)
    if settings.experimental_retriever == "tfidf":
        retriever: Retriever = TfidfRetriever(passages)
    else:
        retriever = BM25Retriever(passages)

    outbox = LocalDemoOutbox(settings.demo_outbox_path, settings.demo_recipient_phone)
    return ApplicationService(
        classifier,
        retriever,
        max_question_codepoints=settings.max_question_codepoints,
        demo_enabled=settings.demo_enabled,
        demo_recipient_phone=settings.demo_recipient_phone,
        demo_outbox=outbox,
        approved_passages=passages,
    )
