"""Study Buddy API for flashcard generation and model connectivity."""

import io
import json
import os
import socket
from collections import defaultdict

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

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


# Flashcards are temporary until a later milestone adds saved decks.
MIN_CARDS = 5
MAX_CARDS = 20
CARD_COUNTS = (MIN_CARDS, 10, MAX_CARDS)
MAX_PDF_BYTES = 8 * 1024 * 1024
MAX_PAGES = 30
MAX_SOURCE_CHARS = 12000


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


def model_text(prompt: str) -> str:
    """Call the same private llama.cpp chat endpoint used by /chat."""
    try:
        response = httpx.post(
            f"{LLM_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 850,
            },
            timeout=240,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError("empty completion")
        return text
    except httpx.TimeoutException as err:
        raise HTTPException(status_code=504, detail="The AI model timed out. Please try again.") from err
    except httpx.ConnectError as err:
        raise HTTPException(status_code=502, detail="Could not connect to the AI model. Please try again.") from err
    except httpx.HTTPStatusError as err:
        raise HTTPException(status_code=502, detail="The AI model rejected the request. Please try again.") from err
    except httpx.HTTPError as err:
        raise HTTPException(status_code=502, detail="The AI model is unavailable. Please try again.") from err
    except (ValueError, KeyError, IndexError, TypeError) as err:
        raise HTTPException(status_code=502, detail="The AI model returned an invalid response.") from err


class CardOutputError(ValueError):
    """The model did not return a usable JSON card array."""


def parse_cards(text: str) -> list[dict[str, str]]:
    """Keep cards with valid question and answer text from a JSON array."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise CardOutputError("malformed JSON") from err
    if not isinstance(data, list):
        raise CardOutputError("expected a JSON array")
    results = []
    for card in data:
        if not isinstance(card, dict):
            continue
        question = card.get("question")
        answer = card.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            continue
        question, answer = question.strip(), answer.strip()
        if 5 <= len(question) <= 240 and 2 <= len(answer) <= 400:
            results.append({"question": question, "answer": answer})
    return results


def is_duplicate_card(card: dict[str, str], existing: list[dict[str, str]]) -> bool:
    question = card["question"].strip().casefold()
    return any(question == item["question"].strip().casefold() for item in existing)


def generate_cards(
    source: str,
    count: int,
    from_topic: bool = False,
) -> list[dict[str, str]]:
    """Generate flashcards from one capped source in a single model request."""
    grounding = (
        "Use only established facts about the topic. "
        if from_topic else
        "For notes or PDFs, use only the supplied material. "
    )
    prompt = (
        "Create concise, factual flashcards. "
        + grounding
        + "Avoid repeating the same question. "
        + f"Return exactly {count} cards as a JSON array. Each card must have string "
        "fields named question and answer. Return no markdown or other text.\n\n"
        + f"STUDY MATERIAL:\n{source[:MAX_SOURCE_CHARS]}"
    )
    try:
        candidates = parse_cards(model_text(prompt))
    except CardOutputError as err:
        raise HTTPException(
            status_code=502,
            detail="The AI returned invalid flashcard data. Please try again.",
        ) from err

    cards = []
    for card in candidates:
        if not is_duplicate_card(card, cards):
            cards.append(card)
    if not cards:
        raise HTTPException(
            status_code=502,
            detail="The AI could not produce usable flashcards. Please try again or provide more study material.",
        )
    return cards


@app.post("/generate")
async def generate(
    mode: str = Form(...),
    count: str = Form("auto"),
    topic: str = Form(""),
    notes: str = Form(""),
    file: UploadFile | None = File(None),
) -> dict:
    if count != "auto" and count not in {str(value) for value in CARD_COUNTS}:
        raise HTTPException(status_code=422, detail="Choose AI Recommended, 5, 10, or 20 cards.")
    if mode not in {"topic", "notes", "pdf"}:
        raise HTTPException(status_code=422, detail="Choose a topic, notes, or PDF.")

    if mode == "pdf":
        if file is None or not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Upload a PDF file.")
        raw = await file.read(MAX_PDF_BYTES + 1)
        if len(raw) > MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail="PDF must be 8 MB or smaller.")
        if not raw.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")
        try:
            reader = PdfReader(io.BytesIO(raw))
            if len(reader.pages) > MAX_PAGES:
                raise HTTPException(status_code=400, detail="PDF must have 30 pages or fewer.")
            sections = []
            for page in reader.pages:
                text = (page.extract_text() or "").strip()
                if text:
                    sections.append(text)
        except HTTPException:
            raise
        except Exception as err:
            raise HTTPException(status_code=400, detail="Could not read this PDF.") from err
        label = file.filename
        source = "\n\n".join(sections)
    elif mode == "notes":
        source = notes.strip()
        label = "Your notes"
    else:
        source = topic.strip()
        label = topic.strip()[:80]

    source = source[:MAX_SOURCE_CHARS]
    if len(source.strip()) < 12:
        if mode == "pdf":
            raise HTTPException(
                status_code=400,
                detail="No readable text was extracted. Upload a PDF with selectable text.",
            )
        raise HTTPException(status_code=400, detail="Add more study material before generating.")
    requested_count = None if count == "auto" else int(count)
    target_count = (
        min(MAX_CARDS, max(MIN_CARDS, (len(source) + 499) // 500))
        if requested_count is None
        else requested_count
    )
    cards = generate_cards(source, target_count, from_topic=(mode == "topic"))
    message = None
    if len(cards) < target_count:
        kind = "recommended" if requested_count is None else "requested"
        message = f"Generated {len(cards)} of {target_count} {kind} cards."
    return {
        "title": label,
        "cards": cards,
        "count": len(cards),
        "requested_count": requested_count,
        "recommended": requested_count is None,
        "message": message,
    }