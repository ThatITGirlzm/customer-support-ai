from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings


def test_default_settings_are_prototype_only_and_input_limit_is_provisional(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for name in (
        "AVESE_MAX_QUESTION_CODEPOINTS",
        "AVESE_EXPERIMENTAL_RETRIEVER",
        "AVESE_DEMO_MODE",
        "AVESE_DEMO_RECIPIENT_PHONE",
        "AVESE_DEMO_OUTBOX_PATH",
        "AVESE_CORS_ORIGINS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_environment(project_root=tmp_path)
    assert settings.max_question_codepoints == 2000
    assert settings.max_question_codepoints_is_provisional is True
    assert settings.experimental_retriever == "tfidf"
    assert settings.demo_enabled is False
    assert settings.demo_recipient_phone is None


def test_owner_configured_limit_remains_provisional_until_policy_approval(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AVESE_MAX_QUESTION_CODEPOINTS", "400")
    settings = Settings.from_environment(project_root=tmp_path)
    assert settings.max_question_codepoints == 400
    assert settings.max_question_codepoints_is_provisional is True


def test_demo_recipient_is_validated_and_hidden_from_settings_repr(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    recipient = "+15555550123"
    monkeypatch.setenv("AVESE_DEMO_RECIPIENT_PHONE", recipient)
    settings = Settings.from_environment(project_root=tmp_path)
    assert settings.demo_recipient_phone == recipient
    assert recipient not in repr(settings)


def test_invalid_phone_and_wildcard_cors_are_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AVESE_DEMO_RECIPIENT_PHONE", "not-a-phone")
    with pytest.raises(ValueError, match="international-format"):
        Settings.from_environment(project_root=tmp_path)

    monkeypatch.delenv("AVESE_DEMO_RECIPIENT_PHONE")
    monkeypatch.setenv("AVESE_CORS_ORIGINS", "*")
    with pytest.raises(ValueError, match="wildcard"):
        Settings.from_environment(project_root=tmp_path)
