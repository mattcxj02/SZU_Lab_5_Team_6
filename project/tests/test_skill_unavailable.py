"""Task 1/4 -- missing knowledge must not be reported as a successful answer.

Regression: asking "Who is the current president of Shenzhen University?"
returned status "success" because qwen3 replied "The information is not
available ..." while the skill matched the exact sentence "That information
is not available ...". The refusal text was right but the status was wrong,
so the audit log and API contract both claimed success.

ask_llm is patched, so these run without Ollama.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skills import campus, library
from skills.base import NOT_AVAILABLE, is_unavailable


class UnavailableDetectionTests(unittest.TestCase):
    def test_matches_the_exact_canonical_sentence(self):
        self.assertTrue(is_unavailable(NOT_AVAILABLE))

    def test_matches_the_paraphrase_that_caused_the_regression(self):
        self.assertTrue(
            is_unavailable("The information is not available in the starter knowledge base.")
        )

    def test_matches_regardless_of_case_and_spacing(self):
        self.assertTrue(
            is_unavailable("This information is  NOT Available\nin the starter knowledge base.")
        )

    def test_does_not_match_a_real_answer(self):
        self.assertFalse(is_unavailable("The motto is self-reliance, self-discipline, self-improvement."))
        self.assertFalse(is_unavailable("Shenzhen University was established in 1983."))


class SkillUnavailableStatusTests(unittest.TestCase):
    def test_campus_reports_unavailable_for_a_paraphrased_refusal(self):
        paraphrase = "The information is not available in the starter knowledge base."
        with patch.object(campus, "ask_llm", return_value=paraphrase):
            result = campus.handle("Who is the current president of Shenzhen University?")

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.response, NOT_AVAILABLE, "response should be canonicalised")

    def test_library_reports_unavailable_for_a_paraphrased_refusal(self):
        paraphrase = "This information is not available in the starter knowledge base."
        with patch.object(library, "ask_llm", return_value=paraphrase):
            result = library.handle("What are the library opening hours?")

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.response, NOT_AVAILABLE)

    def test_a_real_answer_is_still_success_and_passed_through(self):
        answer = "The motto is self-reliance, self-discipline, self-improvement."
        with patch.object(campus, "ask_llm", return_value=answer):
            result = campus.handle("What is the motto?")

        self.assertEqual(result.status, "success")
        self.assertEqual(result.response, answer)


if __name__ == "__main__":
    unittest.main()
