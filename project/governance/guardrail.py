"""Guardrail: reject prompt-injection and unsafe requests before they reach a Skill."""

from __future__ import annotations

import re
from dataclasses import dataclass

_BLOCKED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore (all|any|the|previous|prior)\s+(instructions|rules|prompt)",
        r"disregard (all|any|the|previous|prior)\s+(instructions|rules|prompt)",
        r"forget (all|everything|your instructions|the (system )?prompt)",
        r"reveal (your|the)\s+(system prompt|prompt|instructions)",
        r"show (private|confidential|internal)\s+data",
        r"bypass (safety|the filters?|restrictions)",
        r"you are now (?!a translator)",
        r"jailbreak",
        r"act as (?:dan|an unrestricted)",
    )
]


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str | None = None


def check_guardrail(message: str) -> GuardrailResult:
    """Return GuardrailResult(allowed=False, reason=...) if the message matches a
    known prompt-injection / unsafe-request pattern, else allowed=True."""
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(message):
            return GuardrailResult(allowed=False, reason=f"matched blocked pattern: {pattern.pattern}")
    return GuardrailResult(allowed=True)
