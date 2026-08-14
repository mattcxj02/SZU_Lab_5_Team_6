"""Logic-level Runtime tests.  They do not start Ollama or call an LLM."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.router import SkillRouter
from runtime.service import FAILED_RESPONSE, UNMATCHED_RESPONSE, Runtime
from skills.base import SkillResult


class RuntimeTests(unittest.TestCase):
    def test_routes_library_request_to_library_skill(self) -> None:
        runtime = Runtime()
        self.assertEqual(runtime._router.select("Where is the library?").NAME, "library")

    def test_routes_translation_before_other_matching_skills(self) -> None:
        runtime = Runtime()
        self.assertEqual(
            runtime._router.select("Translate this library notice into Chinese.").NAME,
            "translation",
        )

    def test_routes_campus_request_to_campus_skill(self) -> None:
        runtime = Runtime()
        self.assertEqual(runtime._router.select("When was Shenzhen University founded?").NAME, "campus")

    def test_unmatched_request_has_predictable_result(self) -> None:
        result = Runtime().handle("Tell me a joke about the weather.")
        self.assertEqual(result.status, "unmatched")
        self.assertIsNone(result.skill)
        self.assertEqual(result.response, UNMATCHED_RESPONSE)

    # The Runtime now enforces role-based permissions before executing a
    # Skill, so these fakes use a permitted skill name / role pair.
    def test_skill_result_is_returned_unchanged(self) -> None:
        fake = SimpleNamespace(
            NAME="library",
            can_handle=lambda message: True,
            handle=lambda message: SkillResult("library", "success", "done"),
        )
        result = Runtime(SkillRouter((fake,))).handle("anything", role="member")
        self.assertEqual((result.skill, result.status, result.response), ("library", "success", "done"))

    def test_skill_exception_becomes_error_result(self) -> None:
        def explode(message: str):
            raise RuntimeError("boom")

        broken = SimpleNamespace(NAME="library", can_handle=lambda message: True, handle=explode)
        result = Runtime(SkillRouter((broken,))).handle("anything", role="member")
        self.assertEqual((result.skill, result.status, result.response), ("library", "error", FAILED_RESPONSE))


if __name__ == "__main__":
    unittest.main()
