"""Strict request and response contracts for the prototype API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


Action = Literal[
    "ANSWER_FROM_SOURCE",
    "ABSTAIN_NOT_IN_SOURCES",
    "REFER_HUMAN",
    "DECLINE_OUT_OF_SCOPE",
    "BLOCK_INJECTION",
    "INVALID_REQUEST",
    "SERVICE_UNAVAILABLE",
]


class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: StrictStr


class DemoComplaintRequest(ProcessRequest):
    demo_declaration: Literal["SYNTHETIC_DEMO_ONLY"]


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passage_id: str
    source_id: str
    source_title: str
    source_url: str
    publication_date: str | None = None
    accessed_date: str
    section_or_page: str


class DemonstrationStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    complaint_id: str | None
    record_state: Literal["RECORDED_LOCAL_ONLY", "NOT_RECORDED"]
    notification_state: Literal["QUEUED_LOCAL_ONLY", "NOT_QUEUED"]
    notification_delivered: Literal[False] = False
    external_referral_submitted: Literal[False] = False


class ProcessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    action: Action
    response_text: str
    intent: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    reason_code: str | None = None
    referral_state: Literal["NOT_SENT", "SUBMITTED", "DELIVERY_UNCONFIRMED"] | None = None
    referral_reference: str | None = None
    demonstration: DemonstrationStatus | None = None
