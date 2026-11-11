"""Study Buddy API entry point."""

from fastapi import FastAPI

app = FastAPI(title="Study Buddy API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}