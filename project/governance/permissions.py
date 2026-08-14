"""Role-based permission control (Governance option C / Bonus 2).

Roles are deliberately simple and data-driven: adding a Skill to a role is
a one-line change here, not a code change in the Runtime.

    guest  -> public campus information only
    member -> campus, course, library, translation
    admin  -> every configured skill plus management operations
"""

from __future__ import annotations

DEFAULT_ROLE = "guest"

ROLE_SKILLS: dict[str, set[str]] = {
    "guest": {"campus"},
    "member": {"campus", "course", "library", "translation"},
    "admin": {"campus", "course", "library", "translation", "summary", "admin"},
}


def known_role(role: str) -> bool:
    return role in ROLE_SKILLS


def allowed_skills(role: str) -> set[str]:
    """Skills a role may use. An unknown role is treated as the least
    privileged role rather than being granted everything."""
    return ROLE_SKILLS.get(role, ROLE_SKILLS[DEFAULT_ROLE])


def is_allowed(role: str, skill: str) -> bool:
    return skill in allowed_skills(role)
