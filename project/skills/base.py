"""Shared contract every Skill implements.

Runtime/Router teammate depends on this shape:
    if skill.can_handle(message):
        result = skill.handle(message)

Keep this file untouched by everyone except the Skill-design owner,
so it stays the single source of truth for the interface.
"""

from dataclasses import dataclass


@dataclass
class SkillResult:
    skill: str
    status: str  # "success" | "unavailable" | "error"
    response: str


# The canonical wording a knowledge-backed Skill returns when the answer is
# not in its slice of the knowledge base.
NOT_AVAILABLE = "That information is not available in the starter knowledge base."

# qwen3 paraphrases the fixed sentence -- "The information is not available..."
# instead of "That information is not available..." -- which defeats an exact
# match and mislabels a refusal as a successful answer. Match the distinctive
# fragment instead, and let the Skill return the canonical wording so both the
# status and the text stay deterministic.
_UNAVAILABLE_FRAGMENT = "not available in the starter knowledge base"


def is_unavailable(answer: str) -> bool:
    """True when the model reported it cannot answer from the knowledge base."""
    return _UNAVAILABLE_FRAGMENT in " ".join(answer.lower().split())
