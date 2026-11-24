from __future__ import annotations

import json
import sqlite3

from app.demo_outbox import LocalDemoOutbox
from app.schemas import DemoComplaintRequest
from app.service import ApplicationService


class _UnexpectedClassifier:
    def predict_intent(self, question: str) -> str | None:
        raise AssertionError("sensitive demo request must not reach classification")


class _UnexpectedRetriever:
    def search(self, query: str, top_k: int = 3):
        raise AssertionError("sensitive demo request must not reach retrieval")


class _FailingOutbox:
    def record_and_queue(self, complaint_id: str, complaint_details: str):
        raise OSError("synthetic storage failure")


def _demo_service(path, recipient="+15555550123", outbox=None) -> ApplicationService:
    return ApplicationService(
        _UnexpectedClassifier(),
        _UnexpectedRetriever(),
        max_question_codepoints=2000,
        demo_enabled=True,
        demo_recipient_phone=recipient,
        demo_outbox=outbox or LocalDemoOutbox(path, recipient),
    )


def test_synthetic_complaint_is_recorded_and_queued_without_external_referral(tmp_path) -> None:
    database = tmp_path / "demo.sqlite3"
    recipient = "+15555550123"
    details = "Synthetic test: I was scammed and need human help."
    response = _demo_service(database, recipient).process_demo_complaint(
        DemoComplaintRequest(question=details, demo_declaration="SYNTHETIC_DEMO_ONLY")
    )

    assert response.action == "REFER_HUMAN"
    assert response.referral_state == "NOT_SENT"
    assert response.demonstration.complaint_id.startswith("DEMO-")
    assert response.demonstration.record_state == "RECORDED_LOCAL_ONLY"
    assert response.demonstration.notification_state == "QUEUED_LOCAL_ONLY"
    assert response.demonstration.notification_delivered is False
    assert response.demonstration.external_referral_submitted is False
    assert "not been submitted to a bank" in response.response_text
    assert recipient not in response.model_dump_json()

    with sqlite3.connect(database) as connection:
        complaint = connection.execute(
            "SELECT complaint_details, record_state FROM demo_complaints WHERE complaint_id = ?",
            (response.demonstration.complaint_id,),
        ).fetchone()
        notification = connection.execute(
            "SELECT recipient_phone, payload, delivery_state FROM demo_notification_outbox "
            "WHERE complaint_id = ?",
            (response.demonstration.complaint_id,),
        ).fetchone()

    assert complaint == (details, "RECORDED_LOCAL_ONLY")
    assert notification is not None
    assert notification[0] == recipient
    assert notification[2] == "QUEUED_LOCAL_ONLY"
    payload = json.loads(notification[1])
    assert payload["complaint_id"] == response.demonstration.complaint_id
    assert payload["complaint_details"] == details
    assert "NOT AN EXTERNAL REFERRAL" in payload["notice"]


def test_outbox_failure_never_claims_recording_or_delivery(tmp_path, caplog) -> None:
    details = "Synthetic test: I was scammed and need human help. SENSITIVE-MARKER"
    response = _demo_service(
        tmp_path / "unused.sqlite3",
        outbox=_FailingOutbox(),
    ).process_demo_complaint(DemoComplaintRequest(question=details, demo_declaration="SYNTHETIC_DEMO_ONLY"))

    assert response.action == "SERVICE_UNAVAILABLE"
    assert response.referral_state == "NOT_SENT"
    assert response.demonstration.record_state == "NOT_RECORDED"
    assert response.demonstration.notification_state == "NOT_QUEUED"
    assert response.demonstration.notification_delivered is False
    assert response.demonstration.external_referral_submitted is False
    assert "SENSITIVE-MARKER" not in caplog.text
    assert "+15555550123" not in caplog.text


def test_demo_route_does_not_record_ordinary_or_educational_question(tmp_path) -> None:
    database = tmp_path / "demo.sqlite3"
    service = _demo_service(database)
    response = service.process_demo_complaint(
        DemoComplaintRequest(question="For a class, explain what phishing means.", demo_declaration="SYNTHETIC_DEMO_ONLY")
    )

    assert response.action == "ABSTAIN_NOT_IN_SOURCES"
    assert response.reason_code == "NOT_ELIGIBLE_FOR_DEMO_REFERRAL"
    assert not database.exists()


def test_missing_recipient_does_not_create_a_local_record(tmp_path) -> None:
    database = tmp_path / "demo.sqlite3"
    response = _demo_service(database, recipient=None).process_demo_complaint(
        DemoComplaintRequest(question="I was scammed and need human help.", demo_declaration="SYNTHETIC_DEMO_ONLY")
    )

    assert response.action == "SERVICE_UNAVAILABLE"
    assert response.reason_code == "DEMO_RECIPIENT_OR_OUTBOX_NOT_CONFIGURED"
    assert not database.exists()
