# StudyBuddy

Study Buddy turns a topic, pasted notes, or a lecture PDF into interactive AI-generated flashcards. The React interface lets students flip cards, mark what they know, and review session progress. A private Qwen3-1.7B model runs locally through llama.cpp.

## Features

- Generate cards from a topic, pasted notes, or a text-based PDF.
- Let AI recommend up to 20 cards or set a 5, 10, or 20-card target. The backend may return fewer when the source supports fewer distinct cards.
- Flip cards, navigate Previous/Next, mark Got it or Study again, and track progress.
- Sign in or create an account using Amazon Cognito before using protected API operations.
- Keep the model private to the Docker Compose network.
- Keep `GET /health` public; protect `/chat`, `/generate`, and `/usage/{user}` with Cognito access tokens.

Cards and progress are temporary and are not saved yet. Usage identity comes from the verified Cognito `sub`; `/usage/{user}` only returns the signed-in user's counters. PDFs must contain selectable text; OCR is not supported. PDFs are limited to 8 MB and 30 pages. Local CPU generation can take several minutes, and AI-generated facts should be checked against the source material.

## Run locally

Requires Docker Desktop. Create only the Cognito resources after you have AWS credentials configured. Choose a domain prefix that is unique across Cognito in `us-east-1`:

```powershell
terraform -chdir=terraform init
terraform -chdir=terraform apply -var "domain_prefix=your-unique-studybuddy-prefix"
Copy-Item .env.example .env
```

Set the values in `.env` from the Terraform outputs:

| `.env` setting | Terraform output |
|---|---|
| `COGNITO_ISSUER` | `issuer` |
| `COGNITO_CLIENT_ID`, `VITE_COGNITO_CLIENT_ID` | `client_id` |
| `VITE_COGNITO_USER_POOL_ID` | `user_pool_id` |
| `VITE_COGNITO_DOMAIN` | `cognito_domain` without `https://` |

The callback and logout URLs default to `http://localhost:5173/` and must match the Cognito app client's configured URLs. Do not put credentials, passwords, or tokens in `.env.example` or commit your local `.env`.

Then start the app from the repository root:

```powershell
docker compose up --build -d
docker compose ps
```

The first LLM build downloads the Qwen3-1.7B Q4_K_M model (about 1.2 GB) from [QuantFactory on Hugging Face](https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF). Wait for the model service to become healthy, then open http://localhost:5173. The model's port 8000 is private to the Compose network.

Use **Sign in / Sign up** to open Cognito's hosted login page. Create an account and confirm the email, then sign in. The browser sends the Cognito access token only to protected FastAPI routes. `/health` remains public:

```powershell
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:5173/api/health
```

The flashcard form sends authenticated `POST /generate` through the Vite `/api` proxy. Try AI Recommended with the Week 5 Compose/ECR/ECS lecture PDF and verify the generated material against the slides. Direct requests to FastAPI also need `Authorization: Bearer <access-token>`; missing or invalid tokens receive 401. The backend verifies the signature, issuer, expiration, token type, and app client against Cognito's JWKS.

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

Validate the local Compose configuration with `docker compose config`. Backend tests use signed test JWTs and a mocked JWKS key; they do not call AWS. The project owner has also verified real Cognito signup, login, logout, and authenticated flashcard generation with a provisioned user pool and Docker Compose.

## Architecture and future work

React/Vite → Cognito hosted login and FastAPI → private llama.cpp/Qwen3. Cognito user-pool resources are defined in Terraform; the React public app client uses authorization code with PKCE and no client secret. FastAPI verifies Cognito access tokens itself so direct local API requests are protected without API Gateway. PDF text extraction uses `pypdf`; generated cards return directly to the browser. Flashcards and progress remain temporary until Milestone 5 adds persistence. API Gateway and application deployment are later milestones.

## Cognito teardown

When finished, remove only the Cognito resources created by this Terraform configuration:

```powershell
terraform -chdir=terraform destroy -var "domain_prefix=your-unique-studybuddy-prefix"
```

## Course

CS 1660/2060 — Cloud Computing, Fall 2026.
