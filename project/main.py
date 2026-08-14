"""CampusBot launch entry point.

The macOS/Windows launcher always runs this file, so it stays the entry
point -- but all behaviour now lives in the modular packages:

    api/        HTTP layer (request validation, serialisation)
    runtime/    orchestration + skill routing
    skills/     one module per capability
    governance/ guardrail, permissions, audit logging

This file only starts the web service on the host/port the launcher provides.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# The launcher may start this file from any working directory, so make the
# project folder importable before touching the application packages.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn

from api.server import app

__all__ = ["app"]


if __name__ == "__main__":
    host = os.getenv("CAMPUSBOT_HOST", "127.0.0.1")
    port = int(os.getenv("CAMPUSBOT_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
