"""Translation Skill.

Responsibility: translate the text the user asks for. No knowledge base
lookup at all -- this skill never touches knowledge.json, which is itself
evidence of clean separation of responsibility for the report.

Input:  free-text user message containing text to translate
Output: SkillResult(status="success"|"error", response=str)

There is no "unavailable" status for this skill -- translation either
succeeds or the model call fails (status="error").
"""

from __future__ import annotations

from .base import SkillResult
from .llm_client import ask_llm

NAME = "translation"

KEYWORDS = ["translate", "번역", "翻译"]

SYSTEM_PROMPT = (
    "You are the Translation Skill for CampusBot.\n"
    "Translate only the text the user asks you to translate. Do not add "
    "commentary, explanations, or extra facts. Reply with the translation only."
)


def can_handle(message: str) -> bool:
    text = message.lower()
    return any(keyword in text for keyword in KEYWORDS)


def handle(message: str) -> SkillResult:
    try:
        answer = ask_llm(SYSTEM_PROMPT, message)
    except Exception:
        return SkillResult(
            skill=NAME, status="error",
            response="Translation skill failed to reach the model.",
        )

    if not answer:
        return SkillResult(skill=NAME, status="error", response="Empty response from model.")

    return SkillResult(skill=NAME, status="success", response=answer)
