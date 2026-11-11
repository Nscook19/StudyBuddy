# Study Buddy — Project Status

**Last updated:** November 11, 2026  
**Current milestone:** 1 of 8 complete — application foundation  
**Next milestone:** Connect the LLM from Assignment 2 to FastAPI

## Project summary

Study Buddy is a cloud-hosted AI flashcard study app. The planned user flow is: sign up or log in, enter a study topic, generate question-and-answer cards, save a deck, and return later to study it. We are developing and testing locally before deploying on AWS.

## What works now

- React/Vite frontend runs locally on `http://localhost:5173`.
- FastAPI backend runs locally on `http://localhost:8080` and responds to `GET /health` with `{"status":"ok"}`.
- The frontend reaches the backend through the Vite `/api` proxy; `GET http://localhost:5173/api/health` returns `{"status":"ok"}`.
- Docker Compose starts both services on a shared network.
- Backend container runs as a non-root user (`uid=1000(appuser)` was verified).
- Backend uses `uv`, `pyproject.toml`, and `uv.lock` for Python dependencies.
- Backend tests and frontend build have passed; a GitHub Actions CI run was reported as passing.

**Local verification:** On November 11, both health endpoints returned `ok` after initial startup. Requests made immediately after `docker compose up -d` initially failed because the services were not yet ready; retrying succeeded.

## Not implemented yet

- Connecting to the LLM or generating flashcards
- Flashcard UI, deck save/view/delete features
- Cognito sign-up/login and protected API routes
- DynamoDB persistence
- AWS deployment via Terraform (Terraform files are placeholders)
- GitHub Actions ECR image publishing or CloudWatch alarms

## Milestone roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Bootable React + FastAPI foundation, Docker Compose, tests, CI | **Complete** |
| 2 | Connect private LLM container to FastAPI; verify a real response | Next |
| 3 | Generate and display question/answer flashcards | Not started |
| 4 | Cognito sign-up/login and authenticated requests | Not started |
| 5 | DynamoDB saved decks and per-user access | Not started |
| 6 | Deploy AWS resources using Terraform | Not started |
| 7 | ECR publishing, monitoring/alarms, deployment verification | Not started |
| 8 | End-to-end validation and final demo | Not started |

These milestones track major deliverables, not equal-sized amounts of work. Cloud deployment and LLM operation may take more time than the foundation.

## Run locally

Prerequisite: Docker Desktop is running.

From the repository root (where `compose.yaml` lives):

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:5173/api/health
```

Expected health responses: `status: ok` from both requests. Open `http://localhost:5173` and look for **Backend API: Connected**. It can take a few seconds after startup before endpoints become available.

To verify the backend is non-root:

```powershell
docker compose exec backend id
```

To stop everything:

```powershell
docker compose down
```

## How we're implementing it

- Use simple, explainable code; reuse patterns from our assignments and the professor's course examples where appropriate.
- Keep React as the web UI and FastAPI as the API.
- Reuse the Assignment 2 llama.cpp/Qwen + HTTP proxy pattern for the upcoming LLM integration; the model should not expose a host port.
- Keep Terraform resources and production deployment work separate from the minimal local application until ready to integrate.
- Add a small test for each new backend behavior; avoid premature abstractions.


## Reference

See the project proposal (RFC 0001) for planned architecture, AWS services, user flows, and scope. The planned AWS stack includes S3, CloudFront, Cognito, API Gateway, Application Load Balancer, ECS Fargate, ECR, DynamoDB, and CloudWatch.