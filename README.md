# StudyBuddy

A cloud-hosted study application planned for generating and reviewing flashcards from a topic or pasted notes. The current milestone is a small, runnable application foundation.

## Current foundation

- React + Vite frontend
- FastAPI backend with `GET /health`
- Frontend backend status check through the Vite `/api` development proxy
- Docker Compose local development network
- `uv` dependency management and pytest smoke test
- GitHub Actions backend test/container build and frontend build, without AWS credentials

LLM inference, flashcards, authentication, persistence, and AWS deployment are not implemented.

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

Then open:

- Frontend: http://localhost:5173 (shows `Backend API: Connected`)
- Backend: http://localhost:8080/health (returns `{"status":"ok"}`)
- Proxied health check: http://localhost:5173/api/health (returns `{"status":"ok"}`)

Check that the backend runs as a non-root user:

```powershell
docker compose exec backend id
```

Stop the services with `docker compose down`.

## Run checks without Docker

Requires Python 3.14, uv, Node.js 22+, and npm.

From `backend/`:

```powershell
uv sync --group dev
uv run pytest
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
  app/main.py             Health endpoint
  tests/                  Backend smoke tests
compose.yaml              Local frontend/backend services
terraform/                Reserved for infrastructure code
.github/workflows/        CI checks (no deployment)
```

## Course

CS 1660/2060 — Cloud Computing, Fall 2026.
