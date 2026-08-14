"""Task 2 -- Skill Router priority rules.

test_runtime.py covers the three basic routing scenarios. This file covers
the ordering guarantee that makes them hold: the campus skill claims broad
keywords, so a wrong registry order silently misroutes specific requests.

These run against the real skill modules but never execute them, so no
Ollama process is required -- selection only calls can_handle().
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.router import DEFAULT_SKILLS, SkillRouter


class RouterPriorityTests(unittest.TestCase):
    def setUp(self):
        self.router = SkillRouter()

    def _selected(self, message):
        skill = self.router.select(message)
        return skill.NAME if skill else None

    def test_unrelated_request_is_not_misrouted(self):
        self.assertIsNone(self._selected("What is the weather in Tokyo tomorrow?"))
        self.assertIsNone(self._selected("Write me a Python quicksort."))

    def test_specific_skills_win_over_broad_campus_keywords(self):
        # Both messages contain "university", which the campus skill claims.
        # Registry ordering must still send them to the more specific skill.
        self.assertEqual(self._selected("Where is Shenzhen University Library?"), "library")
        self.assertEqual(
            self._selected('Translate "Welcome to Shenzhen University" into Chinese.'),
            "translation",
        )

    def test_campus_is_ordered_last_so_it_cannot_shadow_others(self):
        self.assertEqual(DEFAULT_SKILLS[-1].NAME, "campus")

    def test_chinese_requests_route_like_the_english_baseline(self):
        # The lab baseline includes a Chinese question ("深圳大学是哪一年成立的？"),
        # so the skills must claim their Chinese keywords too, and the same
        # priority rules must hold for Chinese input.
        self.assertEqual(self._selected("深圳大学是哪一年成立的？"), "campus")
        self.assertEqual(self._selected("深圳大学图书馆在哪里？"), "library")
        self.assertEqual(
            self._selected('把"Welcome to Shenzhen University"翻译成中文。'),
            "translation",
        )


if __name__ == "__main__":
    unittest.main()
