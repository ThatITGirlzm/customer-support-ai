"""Environment-backed settings for the local Averse prototype."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


_DEFAULT_MAX_QUESTION_CODEPOINTS = 2000
_PHONE_PATTERN = re.compile(r"^\+[1-9][0-9]{7,14}$")
_DEFAULT_LOCAL_CORS_ORIGINS = (
    "http://localhost:8081",
    "http://127.0.0.1:8081",
)


def _boolean(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


@dataclass(frozen=True)
class Settings:
    project_root: Path
    max_question_codepoints: int
    max_question_codepoints_is_provisional: bool
    experimental_retriever: str
    demo_enabled: bool
    demo_recipient_phone: str | None = field(repr=False)
    demo_outbox_path: Path
    cors_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls, project_root: Path | None = None) -> "Settings":
        root = project_root or Path(__file__).resolve().parent.parent
        raw_limit = os.getenv("AVESE_MAX_QUESTION_CODEPOINTS")
        provisional = True
        try:
            limit = int(raw_limit) if raw_limit is not None else _DEFAULT_MAX_QUESTION_CODEPOINTS
        except ValueError as exc:
            raise ValueError("AVESE_MAX_QUESTION_CODEPOINTS must be a positive integer") from exc
        if limit < 1:
            raise ValueError("AVESE_MAX_QUESTION_CODEPOINTS must be a positive integer")

        retriever = os.getenv("AVESE_EXPERIMENTAL_RETRIEVER", "tfidf").strip().casefold()
        if retriever not in {"tfidf", "bm25"}:
            raise ValueError("AVESE_EXPERIMENTAL_RETRIEVER must be tfidf or bm25")

        recipient = os.getenv("AVESE_DEMO_RECIPIENT_PHONE")
        if recipient is not None:
            recipient = recipient.strip() or None
        if recipient is not None and not _PHONE_PATTERN.fullmatch(recipient):
            raise ValueError("AVESE_DEMO_RECIPIENT_PHONE must be an international-format phone number")

        local_app_data = os.getenv("LOCALAPPDATA")
        local_base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
        raw_outbox = os.getenv("AVESE_DEMO_OUTBOX_PATH")
        outbox_path = Path(raw_outbox).expanduser() if raw_outbox else (
            local_base / "Averse" / "demo-outbox.sqlite3"
        )

        raw_origins = os.getenv("AVESE_CORS_ORIGINS")
        origins = (
            _DEFAULT_LOCAL_CORS_ORIGINS
            if raw_origins is None
            else tuple(
                origin.strip().rstrip("/")
                for origin in raw_origins.split(",")
                if origin.strip()
            )
        )
        if "*" in origins:
            raise ValueError("AVESE_CORS_ORIGINS must list explicit origins, not a wildcard")

        return cls(
            project_root=root.resolve(),
            max_question_codepoints=limit,
            max_question_codepoints_is_provisional=provisional,
            experimental_retriever=retriever,
            demo_enabled=_boolean("AVESE_DEMO_MODE", False),
            demo_recipient_phone=recipient,
            demo_outbox_path=outbox_path,
            cors_origins=origins,
        )
