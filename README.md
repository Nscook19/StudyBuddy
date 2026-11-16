# StudyBuddy

Study Buddy turns a topic, pasted notes, or a lecture PDF into interactive AI-generated flashcards. The React interface lets students flip cards, mark what they know, and review session progress. A private Qwen3-1.7B model runs locally through llama.cpp.

## Features

- Generate cards from a topic, pasted notes, or a text-based PDF.
- Let AI recommend up to 20 cards or set a 5, 10, or 20-card target. The backend may return fewer when the source supports fewer distinct cards.
- Flip cards, navigate Previous/Next, mark Got it or Study again, and track progress.
- Keep the model private to the Docker Compose network.
- Preserve `GET /health`, `POST /chat`, and `GET /usage/{user}`.

Cards and progress are temporary and are not saved. PDFs must contain selectable text; OCR is not supported. PDFs are limited to 8 MB and 30 pages. Local CPU generation can take several minutes, and AI-generated facts should be checked against the source material.

## Run locally

Requires Docker Desktop. From the repository root:

```powershell
docker compose up --build -d
docker compose ps
```

The first LLM build downloads the Qwen3-1.7B Q4_K_M model (about 1.2 GB) from [QuantFactory on Hugging Face](https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF). Wait for the model service to become healthy, then open http://localhost:5173. The model's port 8000 is private to the Compose network.

Check health and the original chat endpoints:

```powershell
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:5173/api/health
Invoke-RestMethod http://localhost:8080/chat -Method Post -ContentType 'application/json' -Body '{"user":"student","message":"Reply with hello."}'
Invoke-RestMethod http://localhost:8080/usage/student
```

The flashcard form sends `POST /generate` through the Vite `/api` proxy. Try AI Recommended with the Week 5 Compose/ECR/ECS lecture PDF and verify the generated material against the slides.

Stop the services with `docker compose down`.

## Run checks without Docker

Requires Python 3.14, uv, Node.js 22+, and npm.

From `backend/`:

```powershell
uv lock
uv sync --locked --group dev
uv run --locked pytest
```

From `frontend/`:

```powershell
npm install
npm run build
```

The backend tests mock model responses. Verify real inference separately through Docker Compose.

## Architecture and future work

React/Vite → FastAPI → private llama.cpp/Qwen3. PDF text extraction uses `pypdf`; generated cards return directly to the browser. The service has no user accounts or saved decks yet. Authentication, persistence, and AWS deployment are reserved for later milestones. Terraform is not used to provision resources in this milestone.

## Course

CS 1660/2060 — Cloud Computing, Fall 2026.
