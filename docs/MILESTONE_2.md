# Milestone 2: local LLM integration

**Goal:** Prove that FastAPI can send a request to a private llama.cpp model
container and return the model's response. This is not flashcard generation.

## Components

- FastAPI `/chat` forwards messages to the model service through HTTP.
- The llama.cpp container runs Qwen3-1.7B Q4_K_M for this connectivity milestone.
- Docker Compose keeps the model private and waits for its health check.
- The backend uses a non-root image and locked `uv` dependencies.

## Setup (PowerShell, from repository root)

Update the dependency lockfile before building Docker, because the
existing backend Dockerfile runs `uv sync --frozen`:

```powershell
cd backend
uv lock
uv sync --locked --group dev
uv run --locked pytest
cd ..

docker compose up --build -d
docker compose ps
```

The model image downloads roughly 1.28 GB of model weights on the first build,
so this can take longer than Milestone 1. Wait until `llm` is healthy.

## Test (PowerShell)

```powershell
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:5173/api/health
Invoke-RestMethod http://localhost:8080/chat -Method Post -ContentType 'application/json' -Body '{"user":"student","message":"Reply with hello."}'
Invoke-RestMethod http://localhost:8080/usage/student

docker compose ps
docker compose exec backend id
docker compose exec llm id
docker compose logs --tail=50 llm
```

Expected: both health checks return `status: ok`; `/chat` returns a nonempty
`reply`, a `usage` object, and `served_by`; `/usage/student` shows one or more
requests; neither container runs as UID 0. The original React page continues
to show `Backend API: Connected` and is not yet a chat interface.

Verify the model port is not published with `docker compose ps`: the `llm`
service should have no `0.0.0.0:8000->...` host mapping.

Stop: `docker compose down` (keeps images and the frontend dependency volume).

## Scope and caveats

- No flashcard generation, UI chat box, authentication, database, or AWS deployment yet.
- The token counters are in memory; they reset when the backend container restarts.
- `/chat` is deliberately unauthenticated for local testing only. Do not
  expose it to the public internet or deploy it without authentication and rate limits.
- Evaluate structured-flashcard quality in Milestone 3.
- GitHub CI builds only the backend container and uses a mocked model for API unit tests, to avoid large model downloads.
