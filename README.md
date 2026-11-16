# StudyBuddy

A cloud-hosted study application planned for generating and reviewing flashcards from a topic or pasted notes. The current milestone connects the local application to a private llama.cpp model.

## Current foundation

- React + Vite frontend
- FastAPI backend with `GET /health`, a model-proxy `POST /chat`, and in-memory usage counters
- Frontend backend status check through the Vite `/api` development proxy
- Docker Compose local development network with a private Qwen3-1.7B Q4_K_M llama.cpp service
- `uv` dependency management and pytest smoke test
- GitHub Actions backend test/container build and frontend build, without AWS credentials

Flashcard generation, authentication, persistence, and AWS deployment are not implemented.

Project status notes for the team are in [PROJECT_STATUS.md](./PROJECT_STATUS.md).

## Planned features

- Student sign-up and login
- Generate flashcard decks from a topic or notes
- Save, view, study, and delete personal decks

## Planned architecture

The React frontend is planned for Amazon S3 and CloudFront. Amazon Cognito will manage authentication. Requests will reach a FastAPI backend through API Gateway, with the containerized backend hosted on ECS Fargate and its image stored in ECR. DynamoDB will persist flashcard decks. Lambda will handle a separate deck-maintenance operation, and CloudWatch will provide alarms and/or dashboards.

Terraform will define the AWS infrastructure, while GitHub Actions will automate container builds and eventual image publishing. These Terraform files are preserved as the project develops; no AWS resources are provisioned by this foundation.

## Run locally with Docker Compose

Requires Docker Desktop. From the repository root:

```powershell
docker compose up --build -d
```

The first build downloads the Qwen3-1.7B Q4_K_M model. Wait for the `llm` service to become healthy before testing.

Then open:

- Frontend: http://localhost:5173 (shows `Backend API: Connected`)
- Backend: http://localhost:8080/health (returns `{"status":"ok"}`)
- Proxied health check: http://localhost:5173/api/health (returns `{"status":"ok"}`)

Check that the backend runs as a non-root user:

```powershell
docker compose exec backend id
docker compose exec llm id
```

Send a test prompt and inspect usage:

```powershell
Invoke-RestMethod http://localhost:8080/chat -Method Post -ContentType 'application/json' -Body '{"user":"student","message":"Reply with hello."}'
Invoke-RestMethod http://localhost:8080/usage/student
```

The model service is private to the Compose network; port 8000 is not published on the host. The usage counters are in memory and reset on backend restart.

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

Run the backend with `uv run uvicorn app.main:app --reload --port 8080` and the frontend with `npm run dev`. The frontend proxies `/api/health` to the backend.

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
