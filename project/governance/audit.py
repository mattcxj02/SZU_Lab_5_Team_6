"""Audit logging: record basic execution information as JSON lines.

Only metadata is recorded (user, skill, status, duration, a short optional
detail string) -- never the raw user message or model response -- so the
log stays useful for governance review without accumulating sensitive
conversation content.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "audit.log"


@dataclass(frozen=True)
class AuditRecord:
    timestamp: str
    user: str
    skill: str
    status: str  # "success" | "unavailable" | "error" | "blocked" | "unmatched" | "forbidden"
    duration_ms: float
    detail: str | None = None


class AuditLogger:
    def __init__(self, log_path: Path | None = None) -> None:
        self.log_path = log_path or DEFAULT_LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        user: str,
        skill: str,
        status: str,
        duration_ms: float,
        detail: str | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user=user,
            skill=skill,
            status=status,
            duration_ms=round(duration_ms, 2),
            detail=detail,
        )
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        return record


default_logger = AuditLogger()
