# StudyBuddy

A cloud-hosted study application planned for generating and reviewing flashcards from a topic or pasted notes. Milestone 2 is complete: FastAPI now proxies requests to a private Qwen3 model running locally through llama.cpp.

## Current functionality

- React + Vite frontend
- FastAPI backend with `GET /health`, `POST /chat`, and in-memory per-user usage counters at `GET /usage/{user}`
- Frontend backend status check through the Vite `/api` development proxy
- Docker Compose runs the frontend, backend, and private llama.cpp model service
- Qwen3-1.7B Q4_K_M GGUF model, downloaded when building the LLM image (about 1.2 GB)
- `uv` dependency management, backend tests, and GitHub Actions backend/frontend checks

Flashcard generation, authentication, persistence, and AWS deployment are future milestones.

Project status notes for the team are in [PROJECT_STATUS.md](./PROJECT_STATUS.md).

## Model choice

We chose Qwen3-1.7B Q4_K_M as a compact open-weight model for local llama.cpp testing. Its GGUF file is downloaded from [QuantFactory on Hugging Face](https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF) when the LLM image is built. Local inference avoids per-request model API fees, though it still uses local CPU and memory. The API uses an OpenAI-compatible chat endpoint.

## Planned features

- Student sign-up and login
- Generate flashcard decks from a topic or notes
- Save, view, study, and delete personal decks

## Planned architecture

The React frontend is planned for Amazon S3 and CloudFront. Amazon Cognito will manage authentication. Requests will reach a FastAPI backend through API Gateway, with the containerized backend hosted on ECS Fargate and its image stored in ECR. DynamoDB will persist flashcard decks. Lambda will handle a separate deck-maintenance operation, and CloudWatch will provide alarms and/or dashboards.

Terraform is reserved for future AWS infrastructure work; no AWS resources are provisioned by the current application. GitHub Actions tests the backend and builds the backend container and frontend; it does not publish images.

## Run locally with Docker Compose

Requires Docker Desktop. From the repository root, build and start the application:

```powershell
docker compose up --build -d
docker compose ps
```

The first build downloads the Qwen3-1.7B Q4_K_M GGUF model from [QuantFactory's Hugging Face repository](https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF). The model runs with llama.cpp inside the `llm` container. Wait for that service to become healthy before testing. Its port 8000 is available only on the Compose network and is not published to the host.

Open the frontend and check the API:

- Frontend: http://localhost:5173 (shows `Backend API: Connected`)
- Backend: http://localhost:8080/health (returns `{"status":"ok"}`)
- Proxied health check: http://localhost:5173/api/health (returns `{"status":"ok"}`)

Send a prompt and check the in-memory token and request counters:

```powershell
Invoke-RestMethod http://localhost:8080/chat -Method Post -ContentType 'application/json' -Body '{"user":"student","message":"Reply with hello."}'
Invoke-RestMethod http://localhost:8080/usage/student
```

Both backend and LLM containers run as non-root users. Verify with:

```powershell
docker compose exec backend id
docker compose exec llm id
```

Usage counters reset when the backend restarts. `/chat` is unauthenticated and intended for local testing only.

Stop the services with `docker compose down`.

## Run checks without Docker

Requires Python 3.14, uv, Node.js 22+, and npm.

From `backend/`:

```powershell
uv sync --locked --group dev
uv run --locked pytest
```

From `frontend/`:

```powershell
npm install
npm run build
```

Run the backend with `uv run uvicorn app.main:app --reload --port 8080` and the frontend with `npm run dev`. The frontend proxies `/api/health` to the backend. The live model is provided by Docker Compose.

## Repository layout

```text
frontend/                 React UI shell
  src/                    React entry point, page, and styles
backend/                  FastAPI application
  app/main.py             Health, model proxy, and usage endpoints
  tests/                  Backend API tests
llm/                      Private llama.cpp/Qwen model service
compose.yaml              Local frontend/backend/LLM services
terraform/                Reserved for infrastructure code
.github/workflows/        CI checks (no deployment)
```

## Course

CS 1660/2060 — Cloud Computing, Fall 2026.
