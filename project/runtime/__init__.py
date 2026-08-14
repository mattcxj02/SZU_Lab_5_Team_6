"""Request orchestration for CampusBot.

The runtime is intentionally separate from both the HTTP API and individual
Skills.  It receives a message, asks the router to choose a Skill, and
returns one consistent result shape.
"""

from .service import AgentResponse, Runtime

__all__ = ["AgentResponse", "Runtime"]
