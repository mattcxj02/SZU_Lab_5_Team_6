"""Task 3 / Bonus 2 -- role-based permission control."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance.permissions import allowed_skills, is_allowed, known_role


class PermissionTests(unittest.TestCase):
    def test_guest_may_use_campus_only(self):
        self.assertTrue(is_allowed("guest", "campus"))
        self.assertFalse(is_allowed("guest", "library"))
        self.assertFalse(is_allowed("guest", "translation"))

    def test_member_may_use_the_standard_skills(self):
        for skill in ("campus", "library", "translation"):
            self.assertTrue(is_allowed("member", skill), skill)

    def test_admin_has_every_member_skill(self):
        self.assertTrue(allowed_skills("member").issubset(allowed_skills("admin")))

    def test_unknown_role_falls_back_to_least_privilege(self):
        self.assertFalse(known_role("superuser"))
        self.assertEqual(allowed_skills("superuser"), allowed_skills("guest"))
        self.assertFalse(is_allowed("superuser", "translation"))


if __name__ == "__main__":
    unittest.main()
