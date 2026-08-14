"""Library Skill.

Responsibility: library branch locations and the official address.
Only sees the "library" slice of knowledge.json.

Input:  free-text user message
Output: SkillResult(status="success"|"unavailable"|"error", response=str)
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import NOT_AVAILABLE, SkillResult, is_unavailable
from .llm_client import ask_llm

NAME = "library"

KEYWORDS = ["library", "도서관", "图书馆"]

_KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "knowledge.json"
_LIBRARY_KNOWLEDGE = json.loads(
    _KNOWLEDGE_PATH.read_text(encoding="utf-8")
)["library"]

SYSTEM_PROMPT = (
    "You are the Library Skill for CampusBot.\n"
    "Answer only from the knowledge context below. Treat branch names and "
    "addresses as exact facts.\n"
    f"If the context does not contain the answer, reply exactly: \"{NOT_AVAILABLE}\"\n\n"
    "Knowledge context:\n"
    f"{json.dumps(_LIBRARY_KNOWLEDGE, ensure_ascii=False, indent=2)}"
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
            response="Library skill failed to reach the model.",
        )

    if not answer:
        return SkillResult(skill=NAME, status="error", response="Empty response from model.")

    if is_unavailable(answer):
        return SkillResult(skill=NAME, status="unavailable", response=NOT_AVAILABLE)
    return SkillResult(skill=NAME, status="success", response=answer)
