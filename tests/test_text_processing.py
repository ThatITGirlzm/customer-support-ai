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
        ("classes", "class"),
        ("complaining", "complaint"),
        ("running", "run"),
        ("stopped", "stop"),
        ("quickly", "quick"),
        ("licensed", "license"),
        ("licence", "license"),
        ("license", "license"),
        ("licensing", "license"),
        ("regulate", "regulation"),
        ("regulated", "regulation"),
        ("regulation", "regulation"),
        ("regulations", "regulation"),
        ("going", "going"),
        ("class", "class"),
        ("analysis", "analysis"),
        ("news", "news"),
        ("status", "status"),
        ("series", "series"),
        ("always", "always"),
        ("not", "not"),
        ("of", "of"),
        ("", ""),
    ],
)
def test_stem_token_applies_conservative_suffix_rules(word: str, expected: str) -> None:
    """A few clear English endings are reduced without a model library."""
    assert stem_token(word) == expected


def test_complaint_family_normalizes_consistently() -> None:
    """The complaint noun, verb and inflections share a domain stem."""
    assert stem_token("complaints") == "complaint"
    assert stem_token("complaining") == "complaint"
    assert stem_token("complained") == "complaint"
    assert stem_token("complain") == "complaint"
    assert stem_token("complaint") == stem_token("complaining")


def test_licence_family_normalizes_british_and_american_forms() -> None:
    """Licence, license and licensed forms share one spelling-normalized stem."""
    forms = ("licence", "licensed", "license", "licences", "licenses", "licensing")
    assert {stem_token(word) for word in forms} == {"license"}


def test_regulated_and_regulation_share_a_domain_stem() -> None:
    """Verb and noun forms are normalized without merging regulator."""
    assert stem_token("regulated") == stem_token("regulation") == "regulation"
    assert stem_token("regulator") == "regulator"


def test_plural_classes_normalizes_without_changing_singular_class() -> None:
    """The explicit plural exception avoids the incorrect stem ``classe``."""
    assert stem_token("classes") == "class"
    assert stem_token("class") == "class"


def test_unrelated_final_s_words_are_not_truncated() -> None:
    """Conservative plural handling preserves common non-plural final-s words."""
    assert [stem_token(word) for word in ("analysis", "news", "status", "series", "always")] == [
        "analysis", "news", "status", "series", "always"
    ]


def test_preprocess_text_handles_empty_input() -> None:
    """Empty text produces no tokens."""
    assert tokenize("") == []
    assert preprocess_text("") == []


def test_preprocess_text_handles_mixed_case_consistently() -> None:
    """The canonical pipeline normalizes mixed-case text consistently."""
    assert preprocess_text("BaNkS BANKING") == ["bank", "bank"]


def test_preprocess_text_uses_same_domain_normalization_pipeline() -> None:
    """Question tokenization and preprocessing apply all shared lexeme rules."""
    assert preprocess_text("LICENSED licences COMPLAINING classes regulated") == [
        "license", "license", "complaint", "class", "regulation"
    ]


def test_preprocess_text_removes_stop_words_then_stems() -> None:
    """The complete pipeline filters and stems tokens in a predictable order."""
    assert preprocess_text("The complaints are not resolved quickly.") == [
        "complaint",
        "not",
        "resolv",
        "quick",
    ]
