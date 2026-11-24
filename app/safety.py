"""Context-aware, deterministic safety preflight for the prototype.

The rules are deliberately small and auditable. They are not a guarantee that
all unsafe or sensitive wording will be detected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SafetyOutcome(str, Enum):
    CLEAR = "CLEAR"
    BLOCK_INJECTION = "BLOCK_INJECTION"
    REFER_HUMAN = "REFER_HUMAN"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


@dataclass(frozen=True)
class SafetyDecision:
    outcome: SafetyOutcome
    reason_code: str


_QUOTED = re.compile(
    r"""“[^”]*”|‘[^’]*’|"[^"]*"|(?<!\w)'[^']*'""",
    re.DOTALL,
)
_INJECTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|disregard|override|bypass|skip)\b.{0,70}"
        r"\b(?:(?:all|previous|prior|above|the|your|system|source|safety|developer)\s+){0,3}"
        r"(?:instructions?|rules?|polic(?:y|ies)|checks?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:reveal|show|print|repeat|disclose)\b.{0,60}"
        r"\b(?:hidden|system|developer|internal)\b.{0,30}"
        r"\b(?:prompt|instructions?|message|rules?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:pretend|act)\b.{0,40}\b(?:system|developer|admin)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:bypass|disable|turn off)\b.{0,40}\b(?:safety|guardrails?|filters?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:skip|bypass|disable|ignore)\b.{0,45}"
        r"\b(?:referral|human handoff|safety preflight|safety gate|retrieval restrictions?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:retrieve|access|show|use)\b.{0,50}"
        r"\b(?:disabled|restricted|sensitive|fraud|scam)\b.{0,35}"
        r"\b(?:passages?|records?|sources?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:follow|obey|execute)\b.{0,45}\b(?:instructions?|commands?)\b"
        r".{0,25}\b(?:quote|quoted text|above)\b",
        re.IGNORECASE | re.DOTALL,
    ),
)
_HUMAN_HELP_PATTERNS = (
    re.compile(
        r"\b(?:talk|speak|connect|transfer|put me through)\s+(?:to|with)\s+"
        r"(?:a\s+)?(?:human|person|agent|representative|customer support)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:human|person)\s+(?:help|assistance)\b", re.IGNORECASE),
)
_ACTIVE_SENSITIVE_PATTERNS = (
    re.compile(
        r"\b(?:i|we)\s+(?:was|were|got)\s+(?:scammed|defrauded|phished)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:think|suspect|believe)\s+(?:this|that|it)\s+"
        r"(?:is|may be|might be)?\s*(?:a\s+)?(?:scam|fraud|phishing)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:someone|they|a caller|a message)\b.{0,50}"
        r"\b(?:asked|asking|pressured|told)\b.{0,35}\b(?:me|us)\b.{0,45}"
        r"\b(?:otp|one[- ]time code|pin|password|transfer|send money)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:my|our)\s+(?:money|funds)\b.{0,45}"
        r"\b(?:was|were)\s+(?:stolen|taken|transferred)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:sent|shared|gave|entered)\b.{0,45}"
        r"\b(?:otp|one[- ]time code|pin|password)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:report|file)\s+(?:a\s+)?(?:scam|fraud|phishing)\b",
        re.IGNORECASE,
    ),
)
_EDUCATIONAL_PATTERNS = (
    re.compile(
        r"\bfor\s+(?:a\s+)?(?:school|class|lesson|presentation|training|"
        r"awareness|research|security exercise)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:what are scams?|what is (?:a )?scam|what is fraud|what is phishing|"
        r"what does (?:a )?(?:scam|fraud|phishing) mean|how do scams? work|"
        r"how do scammers? work|how does phishing work|define phishing|"
        r"meaning of phishing)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:training example|awareness material|educational discussion)\b",
        re.IGNORECASE,
    ),
)
_NEGATED_REPORT = re.compile(
    r"\b(?:i|we)\s+(?:(?:was|were|am|have)\s+(?:not|never)|"
    r"(?:was|were|have)n['’]t|never\s+(?:was|were|been))\s+"
    r"(?:been\s+)?(?:scammed|defrauded|phished)\b",
    re.IGNORECASE,
)
_QUOTE_EXECUTION = re.compile(
    r"\b(?:follow|obey|execute|apply|carry out)\b.{0,60}\b(?:quote|quoted text|quotation|quoted instructions?)\b",
    re.IGNORECASE | re.DOTALL,
)
_SENSITIVE_MENTION = re.compile(
    r"\b(?:scam(?:s|med)?|fraud|phish(?:ing)?|otp|one[- ]time code|"
    r"payment link)\b",
    re.IGNORECASE,
)


def _matches(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


class SafetyPreflight:
    """Classify only the small set of explicit preflight conditions."""

    def evaluate(self, question: str) -> SafetyDecision:
        if not isinstance(question, str):
            raise TypeError("question must be text")
        quoted_texts = _QUOTED.findall(question)
        unquoted = _QUOTED.sub(" ", question).strip()
        if not unquoted:
            return SafetyDecision(SafetyOutcome.CLEAR, "QUOTED_REFERENCE_ONLY")

        if _matches(_INJECTION_PATTERNS, unquoted) or (
            _QUOTE_EXECUTION.search(unquoted) is not None
            and any(_matches(_INJECTION_PATTERNS, quote) for quote in quoted_texts)
        ):
            return SafetyDecision(SafetyOutcome.BLOCK_INJECTION, "DIRECT_INJECTION_ATTEMPT")

        educational = _matches(_EDUCATIONAL_PATTERNS, unquoted)
        negative = _NEGATED_REPORT.search(unquoted) is not None

        if _matches(_HUMAN_HELP_PATTERNS, unquoted):
            return SafetyDecision(SafetyOutcome.REFER_HUMAN, "EXPLICIT_HUMAN_HELP_REQUEST")

        if _matches(_ACTIVE_SENSITIVE_PATTERNS, unquoted):
            return SafetyDecision(SafetyOutcome.REFER_HUMAN, "DIRECT_SENSITIVE_REPORT")

        if educational or negative:
            return SafetyDecision(SafetyOutcome.CLEAR, "EDUCATIONAL_OR_NEGATED_REFERENCE")

        if _SENSITIVE_MENTION.search(unquoted):
            return SafetyDecision(SafetyOutcome.CLARIFICATION_REQUIRED, "AMBIGUOUS_SENSITIVE_REQUEST")

        reason = "QUOTED_REFERENCE_ONLY" if quoted_texts else "NO_SENSITIVE_SIGNAL"
        return SafetyDecision(SafetyOutcome.CLEAR, reason)
