"""HTTP layer: request validation and serialisation only.

The endpoint does no routing, no prompting and no model access -- it hands
the message to the Runtime and serialises whatever comes back. That is what
keeps the Agent testable without starting a web server.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from runtime import Runtime

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"

# The browser UI does not send a role, and the built-in demo questions cover
# campus, library and translation, so unauthenticated browser traffic is
# treated as "member". "guest" (campus only) is exercised via the API.
WEB_DEFAULT_ROLE = "member"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    user: str = Field(default="anonymous", max_length=64)
    role: str = Field(default=WEB_DEFAULT_ROLE, max_length=32)


class ChatResponse(BaseModel):
    request_id: str
    skill: str | None
    status: str
    response: str
    duration_ms: float


app = FastAPI(title="CampusBot Agent Harness", version="1.0.0")
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")

runtime = Runtime()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = runtime.handle(request.message, user=request.user, role=request.role)
    return ChatResponse(
        request_id=result.request_id,
        skill=result.skill,
        status=result.status,
        response=result.response,
        duration_ms=result.duration_ms,
    )
