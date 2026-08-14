"""Campus Skill.

Responsibility: general Shenzhen University facts (motto, founding year,
campus names). Scope is intentionally narrow -- it only ever sees the
"university" slice of knowledge.json, never the whole file.

Input:  free-text user message
Output: SkillResult(status="success"|"unavailable"|"error", response=str)

Predictable failure behavior: if the model can't answer from the injected
knowledge, it must reply with the fixed "not available" sentence. That
sentence is what flips status to "unavailable" -- this is what proves the
skill doesn't invent facts for things like "who is the president".
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import NOT_AVAILABLE, SkillResult, is_unavailable
from .llm_client import ask_llm

NAME = "campus"

# Broad enough to also catch out-of-scope-but-related questions
# ("president", "international office") so THIS skill demonstrates the
# "missing knowledge -> not available" behavior, instead of falling
# through to the Router's generic "unmatched" path.
KEYWORDS = [
    "motto", "founded", "founding", "established", "campus", "campuses",
    "when was", "university", "president", "office",
    "모토", "설립", "캠퍼스", "총장",
    "深圳大学", "校训", "成立", "校区", "校长",
]

_KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "knowledge.json"
_UNIVERSITY_KNOWLEDGE = json.loads(
    _KNOWLEDGE_PATH.read_text(encoding="utf-8")
)["university"]

SYSTEM_PROMPT = (
    "You are the Campus Info Skill for CampusBot.\n"
    "Answer only from the knowledge context below. Treat names, dates, "
    "mottos, and campus names as exact facts.\n"
    f"If the context does not contain the answer, reply exactly: \"{NOT_AVAILABLE}\"\n\n"
    "Knowledge context:\n"
    f"{json.dumps(_UNIVERSITY_KNOWLEDGE, ensure_ascii=False, indent=2)}"
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
            response="Campus skill failed to reach the model.",
        )

    if not answer:
        return SkillResult(skill=NAME, status="error", response="Empty response from model.")

    if is_unavailable(answer):
        return SkillResult(skill=NAME, status="unavailable", response=NOT_AVAILABLE)
    return SkillResult(skill=NAME, status="success", response=answer)
