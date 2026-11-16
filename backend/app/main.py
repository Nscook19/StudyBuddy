"""Study Buddy API: health check and a simple proxy to the model service.

The /chat route is for testing the model connection; it does not generate flashcards yet.
"""

import os
import socket
from collections import defaultdict

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LLM_URL = os.environ.get("LLM_URL", "http://llm:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen3-1.7b")

app = FastAPI(title="Study Buddy API")

# In-memory usage counters reset when the backend restarts.
USAGE: dict[str, dict[str, int]] = defaultdict(
    lambda: {"prompt_tokens": 0, "completion_tokens": 0, "request_count": 0}
)


class ChatRequest(BaseModel):
    user: str = "student"
    message: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/usage/{user}")
def usage(user: str) -> dict:
    return {"user": user, **USAGE[user]}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    try:
        resp = httpx.post(
            f"{LLM_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": req.message}],
            },
            timeout=120,
        )
        resp.raise_for_status()
    except httpx.HTTPError as err:
        raise HTTPException(status_code=502, detail=f"model unreachable: {err}") from err

    try:
        body = resp.json()
        reply = body["choices"][0]["message"]["content"]
        used = body["usage"]
        prompt_tokens = int(used["prompt_tokens"])
        completion_tokens = int(used["completion_tokens"])
    except (ValueError, KeyError, IndexError, TypeError) as err:
        raise HTTPException(status_code=502, detail="invalid model response") from err

    counters = USAGE[req.user]
    counters["prompt_tokens"] += prompt_tokens
    counters["completion_tokens"] += completion_tokens
    counters["request_count"] += 1

    return {"reply": reply, "usage": used, "served_by": socket.gethostname()}