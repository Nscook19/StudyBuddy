# Study Buddy — Project Status

**Last updated:** November 16, 2026

**Progress:** 4 of 8 milestones complete

| # | Milestone | Status |
|---|---|---|
| 1 | React/FastAPI foundation, Compose, tests, CI | Complete |
| 2 | Private Qwen3 llama.cpp integration and real response verification | Complete |
| 3 | Generate and study flashcards from topics, notes, and PDFs | Complete |
| 4 | Cognito sign-up/login and authenticated requests | Complete |
| 5 | DynamoDB persistence and per-user decks | Not started |
| 6 | AWS deployment using Terraform | Not started |
| 7 | Image publishing and monitoring | Not started |
| 8 | End-to-end validation and final demo | Not started |

Milestone 3 includes a React create/study interface; generation from topics, notes, and text-based PDFs; AI-recommended or fixed 5/10/20-card counts; and review controls with session progress. The 19 backend tests, frontend production build, Compose configuration, and live topic and Week 5 PDF generation checks passed. Cards are temporary until persistence is implemented, and generated facts should be reviewed against the source material.

Milestone 4 adds Cognito-hosted sign-up/sign-in with authorization code and PKCE, browser sign-out, access-token requests, and FastAPI JWT validation. Terraform defines the Cognito user pool, public app client, and hosted login domain. The project owner verified real Cognito signup, login, logout, and authenticated flashcard generation end to end. Saved decks and cross-session persistence remain Milestone 5.
