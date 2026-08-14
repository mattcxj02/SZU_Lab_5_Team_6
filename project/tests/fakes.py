"""Deterministic stand-ins so the Runtime can be tested without Ollama.

A fake skill has the same shape the Router and Runtime rely on:
NAME, can_handle(message), handle(message) -> SkillResult.
"""

from __future__ import annotations

from skills.base import SkillResult


class FakeSkill:
    def __init__(self, name, keywords, status="success", response="ok", raises=False):
        self.NAME = name
        self.keywords = keywords
        self.status = status
        self.response = response
        self.raises = raises
        self.calls: list[str] = []

    def can_handle(self, message: str) -> bool:
        text = message.lower()
        return any(keyword in text for keyword in self.keywords)

    def handle(self, message: str) -> SkillResult:
        self.calls.append(message)
        if self.raises:
            raise RuntimeError("skill exploded")
        return SkillResult(skill=self.NAME, status=self.status, response=self.response)
