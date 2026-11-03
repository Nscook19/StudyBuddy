# AI Flashcard Generator

A cloud-hosted study application for generating and reviewing flashcards from a topic or pasted notes. Students will sign up, generate AI-powered question-and-answer cards, save their decks, and return later to study them.

## Planned features

- Student sign-up and login
- Generate a flashcard deck from a topic or notes
- Save and view personal flashcard decks
- Study cards by flipping between questions and answers
- Delete decks that are no longer needed

## Planned architecture

The React frontend will be delivered through **Amazon S3 and CloudFront**. **Amazon Cognito** will manage authentication. Requests will reach a **FastAPI** backend through **API Gateway**, with the containerized backend hosted on **ECS Fargate** and its image stored in **ECR**. **DynamoDB** will persist flashcard decks. **Lambda** will handle a separate deck-maintenance operation, and **CloudWatch** will provide intentional monitoring through alarms and/or dashboards.

**Terraform** will define the AWS infrastructure, while **GitHub Actions** will automate container builds and image publishing. The precise inference implementation and routing will be finalized during development.

## Repository layout

```text
frontend/                 React UI (placeholder)
  src/components/         Reusable UI components
  src/pages/              Application pages
  src/services/           API/auth clients
backend/                  FastAPI application (placeholder)
  app/api/                API routes
  app/models/             Data models
  app/services/           Application logic
  tests/                  Backend tests
terraform/                Infrastructure as code (placeholder)
  modules/                Reusable Terraform modules
  environments/dev/       Development environment
.github/workflows/        CI/CD workflows (placeholder)
docs/                     Architecture and project notes
scripts/                  Helper scripts
```

## Project status

**Initial repository scaffold only.** Files are intentionally empty and the application is not runnable or deployed yet. The GitHub Actions workflow is a placeholder, not an active pipeline.

## Course

CS 1660/2060 — Cloud Computing, Fall 2026.
