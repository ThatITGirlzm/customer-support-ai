"""Local-only SQLite outbox for synthetic demonstration complaints."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class DemoOutboxUnavailable(RuntimeError):
    """Raised when a local demonstration notification cannot be queued."""


@dataclass(frozen=True)
class DemoOutboxReceipt:
    complaint_id: str
    created_at: str
    notification_state: str = "QUEUED_LOCAL_ONLY"
    notification_delivered: bool = False
    external_referral_submitted: bool = False


class LocalDemoOutbox:
    """Record a synthetic complaint and queue a local-only notification payload.

    This class does not send SMS or contact a bank, BoZ, or a human support team.
    """

    def __init__(self, database_path: Path, recipient_phone: str | None) -> None:
        self.database_path = Path(database_path)
        self._recipient_phone = recipient_phone

    def record_and_queue(self, complaint_id: str, complaint_details: str) -> DemoOutboxReceipt:
        if not self._recipient_phone:
            raise DemoOutboxUnavailable("demonstration recipient is not configured")
        if not complaint_id or not complaint_id.startswith("DEMO-"):
            raise ValueError("complaint ID must be a local demonstration ID")
        if not isinstance(complaint_details, str) or not complaint_details.strip():
            raise ValueError("demonstration details must be non-empty text")

        created_at = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(
            {
                "complaint_id": complaint_id,
                "complaint_details": complaint_details.strip(),
                "notice": "SYNTHETIC DEMONSTRATION ONLY; NOT AN EXTERNAL REFERRAL",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.database_path, timeout=5.0) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS demo_complaints (
                        complaint_id TEXT PRIMARY KEY,
                        complaint_details TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        record_state TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS demo_notification_outbox (
                        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        complaint_id TEXT NOT NULL UNIQUE,
                        recipient_phone TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        queued_at TEXT NOT NULL,
                        delivery_state TEXT NOT NULL,
                        FOREIGN KEY (complaint_id) REFERENCES demo_complaints(complaint_id)
                    )
                    """
                )
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO demo_complaints VALUES (?, ?, ?, ?)",
                    (complaint_id, complaint_details.strip(), created_at, "RECORDED_LOCAL_ONLY"),
                )
                connection.execute(
                    """
                    INSERT INTO demo_notification_outbox
                    (complaint_id, recipient_phone, payload, queued_at, delivery_state)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        complaint_id,
                        self._recipient_phone,
                        payload,
                        created_at,
                        "QUEUED_LOCAL_ONLY",
                    ),
                )
        except (OSError, sqlite3.Error) as exc:
            raise DemoOutboxUnavailable("local demonstration outbox is unavailable") from exc

        return DemoOutboxReceipt(complaint_id=complaint_id, created_at=created_at)
