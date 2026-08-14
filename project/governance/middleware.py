"""Governance middleware: wraps Skill execution with the guardrail + audit log.

Integration contract for the Runtime/Skill Router (Task 1 & 2):

    from governance import run_governed

    result = run_governed(
        user=request.user,
        message=request.message,
        skill_name=selected_skill.name,
        executor=lambda: selected_skill.handle(request.message),
    )

    if not result.allowed:
        # guardrail blocked the request -> result.reason explains why
        ...
    elif result.status == "error":
        # the skill raised -> result.reason has the exception message
        ...
    else:
        # result.result holds whatever the skill returned
        ...

`executor` is only called if the guardrail allows the message, and every
call path (blocked / success / error) is recorded through the audit logger.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from .audit import AuditLogger, default_logger
from .guardrail import check_guardrail


@dataclass(frozen=True)
class GovernedResult:
    allowed: bool
    status: str  # "blocked" | "success" | "unavailable" | "error"
    result: Any
    reason: str | None


def run_governed(
    *,
    user: str,
    message: str,
    skill_name: str,
    executor: Callable[[], Any],
    logger: AuditLogger | None = None,
    status_of: Callable[[Any], str] | None = None,
) -> GovernedResult:
    logger = logger or default_logger
    guard = check_guardrail(message)

    if not guard.allowed:
        logger.record(user=user, skill=skill_name, status="blocked", duration_ms=0.0, detail=guard.reason)
        return GovernedResult(allowed=False, status="blocked", result=None, reason=guard.reason)

    start = time.perf_counter()
    try:
        result = executor()
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any skill failure becomes an observation
        duration_ms = (time.perf_counter() - start) * 1000
        logger.record(user=user, skill=skill_name, status="error", duration_ms=duration_ms, detail=str(exc))
        return GovernedResult(allowed=True, status="error", result=None, reason=str(exc))

    duration_ms = (time.perf_counter() - start) * 1000
    # Skills own their failure modes and report them as a status rather than
    # raising (see skills/base.py), so the audit status comes from the result
    # itself when the caller supplies a `status_of` extractor.
    status = status_of(result) if status_of is not None else "success"
    logger.record(user=user, skill=skill_name, status=status, duration_ms=duration_ms)
    return GovernedResult(allowed=True, status=status, result=result, reason=None)
