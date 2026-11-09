"""Small, deterministic text helpers shared by training and retrieval."""

import re
from typing import Iterable


# Short English function-word list. Negations and question words are
# intentionally excluded because they can affect intent and retrieval.
STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "to",
        "of",
        "in",
        "on",
        "at",
        "by",
        "for",
        "from",
        "with",
        "as",
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
    }
)


# Punctuation separates tokens. Integers and decimal numbers are preserved.
_TOKEN_PATTERN = re.compile(r"[a-z]+|[0-9]+(?:\.[0-9]+)?")


def tokenize(text: str) -> list[str]:
    """Return lowercase English word and number tokens from *text*."""
    return _TOKEN_PATTERN.findall(text.lower())


def remove_stop_words(tokens: Iterable[str]) -> list[str]:
    """Return lowercase tokens after removing the documented stop words."""
    return [token.lower() for token in tokens if token.lower() not in STOP_WORDS]


def _remove_doubled_final_consonant(word: str) -> str:
    """Reduce a doubled final consonant after a suffix is removed."""
    if (
        len(word) > 3
        and word[-1] == word[-2]
        and word[-1] not in "aeiou"
    ):
        return word[:-1]
    return word


def _keep_if_stem_is_long_enough(original: str, candidate: str) -> str:
    """Avoid returning a stem shorter than three characters."""
    return candidate if len(candidate) >= 3 else original


def stem_token(token: str) -> str:
    """Apply a small set of English suffix rules to one token.

    Tokens of three characters or fewer are unchanged. Rules, in order:

    - Plural ``-ies`` becomes ``-y`` (``policies`` -> ``policy``).
    - Plural ``-s`` is removed except from ``-ss`` (``fees`` -> ``fee``).
    - ``-ing`` is removed, then a doubled final consonant is reduced
      (``banking`` -> ``bank``; ``running`` -> ``run``).
    - ``-ed`` is removed, then a doubled final consonant is reduced
      (``licensed`` -> ``licens``; ``stopped`` -> ``stop``).
    - ``-ly`` is removed (``quickly`` -> ``quick``).

    No other endings are changed, and a candidate shorter than three
    characters is discarded.
    """
    word = token.lower()
    if len(word) <= 3:
        return word

    if word.endswith("ies"):
        candidate = word[:-3] + "y"
        return _keep_if_stem_is_long_enough(word, candidate)

    if word.endswith("s") and not word.endswith("ss"):
        candidate = word[:-1]
        return _keep_if_stem_is_long_enough(word, candidate)

    if word.endswith("ing"):
        candidate = _remove_doubled_final_consonant(word[:-3])
        return _keep_if_stem_is_long_enough(word, candidate)

    if word.endswith("ed"):
        candidate = _remove_doubled_final_consonant(word[:-2])
        return _keep_if_stem_is_long_enough(word, candidate)

    if word.endswith("ly"):
        candidate = word[:-2]
        return _keep_if_stem_is_long_enough(word, candidate)

    return word


def preprocess_text(text: str) -> list[str]:
    """Canonical preprocessing for both model training and retrieval queries."""
    return [stem_token(token) for token in remove_stop_words(tokenize(text))]
