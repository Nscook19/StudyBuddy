"""API tests: mock the LLM so GitHub Actions does not need model weights."""

import httpx
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_usage_starts_at_zero():
    response = client.get("/usage/new-student")
    assert response.status_code == 200
    assert response.json()["request_count"] == 0


def test_chat_sends_message_to_model(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == f"{main.LLM_URL}/v1/chat/completions"
        assert json["messages"] == [{"role": "user", "content": "Say hello"}]
        assert json["model"] == main.MODEL_NAME
        assert timeout == 120
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(main.httpx, "post", fake_post)
    result = client.post("/chat", json={"user": "test-student", "message": "Say hello"})
    assert result.status_code == 200
    assert result.json()["reply"] == "Hello!"
    assert result.json()["usage"]["total_tokens"] == 5
    usage = client.get("/usage/test-student").json()
    assert usage["request_count"] >= 1
    assert usage["prompt_tokens"] >= 3


def test_chat_reports_model_unreachable(monkeypatch):
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(main.httpx, "post", fake_post)
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 502
    assert "model unreachable" in response.json()["detail"]


def test_chat_rejects_invalid_model_response(monkeypatch):
    def fake_post(url, json, timeout):
        return httpx.Response(200, json={"choices": []}, request=httpx.Request("POST", url))

    monkeypatch.setattr(main.httpx, "post", fake_post)
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 502
    assert response.json()["detail"] == "invalid model response"
