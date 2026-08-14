"""Runtime orchestration between the API, router, Skills, and Governance.

The Runtime owns the *order of operations* and nothing else.  It does not
know how any Skill answers a question, and no Skill knows it is governed:

    guardrail -> route -> permission -> execute -> audit -> result
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from types import ModuleType
from uuid import uuid4

from governance.audit import AuditLogger, default_logger
from governance.guardrail import check_guardrail
from governance.middleware import run_governed
from governance.permissions import DEFAULT_ROLE, is_allowed

from .router import SkillRouter


UNMATCHED_RESPONSE = "I could not match this request to an available skill."
FAILED_RESPONSE = "The selected skill could not complete this request."
BLOCKED_RESPONSE = "This request was blocked by CampusBot's safety rules."
FORBIDDEN_RESPONSE = "Your role ({role}) is not permitted to use the {skill} skill."

# Audit label for a request that never reached a Skill.
NO_SKILL = "-"


@dataclass(frozen=True)
class AgentResponse:
    """The stable result contract returned to the API layer."""

    skill: str | None
    status: str  # success | unavailable | error | unmatched | blocked | forbidden
    response: str
    request_id: str = ""
    duration_ms: float = 0.0


class Runtime:
    """Coordinate one request without knowing any Skill-specific logic."""

    def __init__(
        self,
        router: SkillRouter | None = None,
        logger: AuditLogger | None = None,
    ) -> None:
        self._router = router or SkillRouter()
        self._logger = logger or default_logger

    def handle(
        self,
        message: str,
        *,
        user: str = "anonymous",
        role: str = DEFAULT_ROLE,
    ) -> AgentResponse:
        """Route and execute ``message`` under governance, including
        predictable fallbacks for blocked, unmatched, forbidden and failed
        requests."""
        request_id = uuid4().hex[:8]
        started = time.perf_counter()

        def elapsed_ms() -> float:
            return round((time.perf_counter() - started) * 1000, 2)

        # Guardrail runs before routing, so an injection attempt never reaches
        # a Skill regardless of which Skill it would have been routed to.
        guard = check_guardrail(message)
        if not guard.allowed:
            self._logger.record(
                user=user, skill=NO_SKILL, status="blocked",
                duration_ms=elapsed_ms(), detail=guard.reason,
            )
            return AgentResponse(None, "blocked", BLOCKED_RESPONSE, request_id, elapsed_ms())

        skill = self._router.select(message)
        if skill is None:
            self._logger.record(
                user=user, skill=NO_SKILL, status="unmatched", duration_ms=elapsed_ms(),
            )
            return AgentResponse(None, "unmatched", UNMATCHED_RESPONSE, request_id, elapsed_ms())

        if not is_allowed(role, skill.NAME):
            self._logger.record(
                user=user, skill=skill.NAME, status="forbidden",
                duration_ms=elapsed_ms(), detail=f"role={role}",
            )
            return AgentResponse(
                skill.NAME, "forbidden",
                FORBIDDEN_RESPONSE.format(role=role, skill=skill.NAME),
                request_id, elapsed_ms(),
            )

        return self._execute(skill, message, user=user, request_id=request_id, elapsed_ms=elapsed_ms)

    def _execute(
        self,
        skill: ModuleType,
        message: str,
        *,
        user: str,
        request_id: str,
        elapsed_ms,
    ) -> AgentResponse:
        # run_governed times the call and writes the audit record. Skills report
        # failure as a status rather than raising, so the audit status comes
        # from the SkillResult; a skill that raises anyway is contained here.
        governed = run_governed(
            user=user,
            message=message,
            skill_name=skill.NAME,
            executor=lambda: skill.handle(message),
            logger=self._logger,
            status_of=lambda result: result.status,
        )

        if governed.result is None:
            return AgentResponse(skill.NAME, "error", FAILED_RESPONSE, request_id, elapsed_ms())

        result = governed.result
        return AgentResponse(result.skill, result.status, result.response, request_id, elapsed_ms())
