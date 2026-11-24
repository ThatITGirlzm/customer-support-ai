"""Small, deterministic text helpers shared by training and retrieval."""

import re
from typing import Iterable


TEXT_PROCESSING_VERSION = "2.0.0"

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


# These compact, project-relevant lexical families need a shared canonical
# form. Exact entries avoid broad rules such as stripping arbitrary ``-tion``
# or changing every word that ends in ``-ence``.
_DOMAIN_NORMALIZATIONS: dict[str, str] = {
    # British/American spelling and inflections of the licensing term.
    "licence": "license",
    "licences": "license",
    "licenced": "license",
    "licensed": "license",
    "license": "license",
    "licenses": "license",
    "licensing": "license",
    "licencing": "license",
    # Complaint noun/verb family.
    "complaint": "complaint",
    "complaints": "complaint",
    "complain": "complaint",
    "complains": "complaint",
    "complained": "complaint",
    "complaining": "complaint",
    # Closely related regulation inflections; keep regulator distinct.
    "regulate": "regulation",
    "regulates": "regulation",
    "regulated": "regulation",
    "regulating": "regulation",
    "regulation": "regulation",
    "regulations": "regulation",
    # These plurals add only ``-s`` to the singular spelling.
    "movies": "movie",
    "cookies": "cookie",
    "analyses": "analysis",
}


# Words whose final s is not a productive plural suffix. The suffix-family
# checks below handle common ``-is``, ``-us`` and ``-ous`` endings; these exact
# words cover common exceptions such as ``news`` and invariant plurals.
_PROTECTED_FINAL_S_WORDS = frozenset(
    {"always", "news", "series", "species"}
)


def tokenize(text: str) -> list[str]:
    """Return lowercase English word and number tokens from *text*."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return _TOKEN_PATTERN.findall(text.casefold())


def remove_stop_words(tokens: Iterable[str]) -> list[str]:
    """Return lowercase tokens after removing the documented stop words."""
    normalized = (token.casefold() for token in tokens)
    return [token for token in normalized if token not in STOP_WORDS]


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
    """Normalize selected domain families, then apply conservative suffix rules.

    Tokens of three characters or fewer are unchanged. Rules, in order:

    - Normalize the explicit licensing, complaint and regulation inflections
      in ``_DOMAIN_NORMALIZATIONS``; ``regulator`` remains separate.
    - Plural ``-ies`` becomes ``-y`` (``policies`` -> ``policy``).
    - Sibilant plurals ending ``-sses``, ``-xes``, ``-ches``, ``-shes`` or
      ``-zes`` lose ``-es`` (``classes`` -> ``class``).
    - Other plural ``-s`` is removed except from protected non-plurals such as
      ``analysis``, ``news``, ``status``, ``series`` and ``always``.
    - ``-ing`` is removed, then a doubled final consonant is reduced
      (``banking`` -> ``bank``; ``running`` -> ``run``).
    - ``-ed`` is removed, then a doubled final consonant is reduced
      (``stopped`` -> ``stop``; ``licensed`` is handled by its exact family).
    - ``-ly`` is removed (``quickly`` -> ``quick``).

    No broad derivational suffixes are stripped. A candidate shorter than
    three characters is discarded.
    """
    if not isinstance(token, str):
        raise TypeError("token must be a string")
    word = token.casefold()
    if len(word) <= 3:
        return word

    normalized = _DOMAIN_NORMALIZATIONS.get(word)
    if normalized is not None:
        return normalized

    # ``analysis`` is a non-plural with an ``-is`` ending, not a regular
    # plural; do not let the general -ies rule reduce it to a malformed stem.
    if word in _PROTECTED_FINAL_S_WORDS or word.endswith(("is", "us", "ous", "ics")):
        return word

    if word.endswith("ies"):
        candidate = word[:-3] + "y"
        return _keep_if_stem_is_long_enough(word, candidate)

    if word.endswith(("sses", "xes", "ches", "shes", "zes")):
        candidate = word[:-2]
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
