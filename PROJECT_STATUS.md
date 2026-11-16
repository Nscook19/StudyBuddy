# Study Buddy — Project Status

**Last updated:** November 16, 2026
**Current milestone:** 2 of 8 complete — private local LLM integration
**Next milestone:** Generate and display question-and-answer flashcards

## Project summary

Study Buddy is a cloud-hosted AI flashcard study app. The planned user flow is: sign up or log in, enter a study topic, generate question-and-answer cards, save a deck, and return later to study it. Development and testing happen locally before any AWS deployment.

## What works now

- React/Vite frontend runs locally on `http://localhost:5173` and reports **Backend API: Connected**.
- FastAPI backend runs locally on `http://localhost:8080`; `GET /health` returns `{"status":"ok"}`.
- `POST /chat` proxies requests to Qwen3-1.7B Q4_K_M running through llama.cpp and returns its response and token usage.
- `GET /usage/{user}` reports in-memory prompt-token, completion-token, and request counters.
- Docker Compose runs the frontend, backend, and private model service on a shared network. The model's port 8000 is not published to the host.
- Backend and LLM containers run as non-root users.
- Backend tests use a mocked LLM, so CI does not need to download model weights.
- Backend dependencies are managed by `uv` and `uv.lock`; frontend production build succeeds.

## Not implemented yet

- Flashcard generation or flashcard UI, deck save/view/delete features
- Cognito sign-up/login and protected API routes
- DynamoDB persistence
- AWS deployment via Terraform (Terraform files are placeholders)
- GitHub Actions ECR image publishing or CloudWatch alarms

## Milestone roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Bootable React + FastAPI foundation, Docker Compose, tests, CI | **Complete** |
| 2 | Connect private LLM container to FastAPI; verify a real response | **Complete** |
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
Invoke-RestMethod http://localhost:8080/chat -Method Post -ContentType 'application/json' -Body '{"user":"student","message":"Reply with hello."}'
Invoke-RestMethod http://localhost:8080/usage/student
```

The first model image build downloads about 1.28 GB of model weights. Wait until the `llm` service is healthy. Open `http://localhost:5173` and look for **Backend API: Connected**.

To verify both containers run as non-root:

```powershell
docker compose exec backend id
docker compose exec llm id
```

The model service has no published host port; only the backend reaches it over the Compose network. The usage counters are in memory and reset when the backend restarts. The unauthenticated `/chat` endpoint is for local testing only.

To stop everything:

```powershell
docker compose down
```

## References

See [Milestone 2 setup and tests](docs/MILESTONE_2.md) for detailed local validation steps and the planned features and AWS architecture in this README.
