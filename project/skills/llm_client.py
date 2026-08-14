"""Single Ollama client shared by every Skill.

This is the only place that talks to the model, so the connection settings
live in one spot and Skills can be tested by patching ``ask_llm`` instead of
starting Ollama.
"""

from __future__ import annotations

import os

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")


def ask_llm(system_prompt: str, user_message: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 4096,
            "seed": 42,
        },
    }
    response = httpx.post(OLLAMA_URL, json=payload, timeout=90)
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "").strip()
