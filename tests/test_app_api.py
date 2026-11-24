from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from app.config import Settings
from app.demo_outbox import LocalDemoOutbox
from app.main import create_app
from app.service import ApplicationService


class _Classifier:
    def predict_intent(self, question: str) -> str | None:
        return "complaints_process"


class _Retriever:
    def search(self, query: str, top_k: int = 3):
        return []


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        project_root=tmp_path,
        max_question_codepoints=2000,
        max_question_codepoints_is_provisional=True,
        experimental_retriever="tfidf",
        demo_enabled=True,
        demo_recipient_phone="+15555550123",
        demo_outbox_path=tmp_path / "demo.sqlite3",
        cors_origins=(),
    )


def _app(tmp_path: Path):
    settings = _settings(tmp_path)
    outbox = LocalDemoOutbox(settings.demo_outbox_path, settings.demo_recipient_phone)
    service = ApplicationService(
        _Classifier(),
        _Retriever(),
        max_question_codepoints=settings.max_question_codepoints,
        demo_enabled=settings.demo_enabled,
        demo_recipient_phone=settings.demo_recipient_phone,
        demo_outbox=outbox,
    )
    return create_app(service, settings)


async def _asgi_request(
    app,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    client: tuple[str, int] = ("127.0.0.1", 5050),
) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    sent_request = False
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        nonlocal sent_request
        if not sent_request:
            sent_request = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"127.0.0.1"), (b"content-type", b"application/json")],
        "client": client,
        "server": ("127.0.0.1", 8000),
    }
    await app(scope, receive, send)
    status = next(message["status"] for message in messages if message["type"] == "http.response.start")
    response_bytes = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return status, json.loads(response_bytes) if response_bytes else {}


def test_health_and_request_routes_are_available_without_testclient(tmp_path) -> None:
    app = _app(tmp_path)
    status, health = asyncio.run(_asgi_request(app, "GET", "/health"))
    assert status == 200
    assert health == {"status": "ok", "mode": "local-prototype"}

    status, response = asyncio.run(
        _asgi_request(
            app,
            "POST",
            "/api/v1/requests",
            {"question": "What does the approved source say about a complaint?"},
        )
    )
    assert status == 200
    assert response["action"] == "ABSTAIN_NOT_IN_SOURCES"
    assert "citations" in response


def test_demo_api_records_locally_and_does_not_expose_recipient(tmp_path) -> None:
    app = _app(tmp_path)
    status, response = asyncio.run(
        _asgi_request(
            app,
            "POST",
            "/api/v1/demo/complaints",
            {
                "question": "Synthetic test: I was scammed and need human help.",
                "demo_declaration": "SYNTHETIC_DEMO_ONLY",
            },
        )
    )
    assert status == 200
    assert response["demonstration"]["record_state"] == "RECORDED_LOCAL_ONLY"
    assert response["demonstration"]["notification_state"] == "QUEUED_LOCAL_ONLY"
    assert response["demonstration"]["notification_delivered"] is False
    assert response["demonstration"]["external_referral_submitted"] is False
    assert "+15555550123" not in json.dumps(response)
    assert "not been submitted to a bank" in response["response_text"]


def test_demo_api_rejects_non_loopback_client(tmp_path) -> None:
    app = _app(tmp_path)
    status, response = asyncio.run(
        _asgi_request(
            app,
            "POST",
            "/api/v1/demo/complaints",
            {
                "question": "Synthetic test: I was scammed and need help.",
                "demo_declaration": "SYNTHETIC_DEMO_ONLY",
            },
            client=("192.0.2.10", 5050),
        )
    )
    assert status == 403
    assert response["detail"] == "Local demonstration access only."


def test_validation_errors_do_not_echo_submitted_values(tmp_path) -> None:
    app = _app(tmp_path)
    status, response = asyncio.run(
        _asgi_request(
            app,
            "POST",
            "/api/v1/requests",
            {"question": {"private-marker": "SENSITIVE-123"}},
        )
    )
    encoded = json.dumps(response)
    assert status == 422
    assert response["action"] == "INVALID_REQUEST"
    assert "private-marker" not in encoded
    assert "SENSITIVE-123" not in encoded
    assert "input" not in encoded
