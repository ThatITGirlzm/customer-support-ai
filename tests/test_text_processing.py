"""Behavior tests for the assistant's small, English-only text pipeline."""

import pytest

from ml.text_processing import (
    STOP_WORDS,
    preprocess_text,
    remove_stop_words,
    stem_token,
    tokenize,
)


def test_tokenize_lowercases_and_splits_punctuation() -> None:
    """Words are lowercased and punctuation separates tokens."""
    assert tokenize("How do I report a scam?") == ["how", "do", "i", "report", "a", "scam"]


def test_tokenize_keeps_integers_and_decimal_numbers() -> None:
    """Numeric content remains available to retrieval."""
    assert tokenize("Use 2 steps and a 10.5 rate.") == ["use", "2", "steps", "and", "a", "10.5", "rate"]


def test_stop_word_filter_removes_common_words() -> None:
    """The explicit English stop-word set filters common function words."""
    assert remove_stop_words(["the", "consumer", "and", "bank"]) == ["consumer", "bank"]


@pytest.mark.parametrize("protected_word", ["no", "not", "never", "how", "what", "where", "when", "who"])
def test_stop_word_filter_preserves_negation_and_question_words(protected_word: str) -> None:
    """Negation and question words remain available to classification and retrieval."""
    assert protected_word not in STOP_WORDS
    assert remove_stop_words([protected_word]) == [protected_word]


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("complaints", "complaint"),
        ("payments", "payment"),
        ("fees", "fee"),
        ("scams", "scam"),
        ("banks", "bank"),
        ("banking", "bank"),
        ("policies", "policy"),
        ("classes", "classe"),
        ("complaining", "complain"),
        ("running", "run"),
        ("stopped", "stop"),
        ("quickly", "quick"),
        ("licensed", "licens"),
        ("licence", "licence"),
        ("going", "going"),
        ("class", "class"),
        ("not", "not"),
        ("of", "of"),
        ("", ""),
    ],
)
def test_stem_token_applies_conservative_suffix_rules(word: str, expected: str) -> None:
    """A few clear English endings are reduced without a model library."""
    assert stem_token(word) == expected


def test_complaint_and_complaining_stem_inconsistently() -> None:
    """The permitted suffix rules leave this noun and verb form different."""
    assert stem_token("complaints") == "complaint"
    assert stem_token("complaining") == "complain"
    assert stem_token("complaint") != stem_token("complaining")


def test_licensed_and_licence_stem_inconsistently() -> None:
    """Simple suffix stripping does not normalize this spelling pair."""
    assert stem_token("licensed") == "licens"
    assert stem_token("licence") == "licence"
    assert stem_token("licensed") != stem_token("licence")


def test_preprocess_text_handles_empty_input() -> None:
    """Empty text produces no tokens."""
    assert tokenize("") == []
    assert preprocess_text("") == []


def test_preprocess_text_handles_mixed_case_consistently() -> None:
    """The canonical pipeline normalizes mixed-case text consistently."""
    assert preprocess_text("BaNkS BANKING") == ["bank", "bank"]


def test_preprocess_text_removes_stop_words_then_stems() -> None:
    """The complete pipeline filters and stems tokens in a predictable order."""
    assert preprocess_text("The complaints are not resolved quickly.") == [
        "complaint",
        "not",
        "resolv",
        "quick",
    ]
