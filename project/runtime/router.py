"""Deterministic Skill selection for CampusBot.

Rules are deliberately simple for the lab: each Skill owns its own
``can_handle`` keywords, while the router defines the priority when a request
matches more than one capability.
"""

from __future__ import annotations

from types import ModuleType

from skills import campus, library, translation


# Translation must take priority so a request such as "Translate this library
# notice" is translated rather than answered as a library question.
DEFAULT_SKILLS: tuple[ModuleType, ...] = (translation, library, campus)


class SkillRouter:
    """Select one Skill for a message, or ``None`` when none applies."""

    def __init__(self, skills: tuple[ModuleType, ...] = DEFAULT_SKILLS) -> None:
        self._skills = skills

    def select(self, message: str) -> ModuleType | None:
        """Return the first Skill whose ``can_handle`` function accepts it."""
        for skill in self._skills:
            if skill.can_handle(message):
                return skill
        return None
