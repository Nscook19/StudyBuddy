"""API tests: mock the LLM so GitHub Actions does not need model weights."""

from datetime import datetime, timedelta, timezone

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)
ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_testpool"
CLIENT_ID = "test-client"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = PRIVATE_KEY.public_key()


@pytest.fixture(autouse=True)
def mock_cognito_jwks(monkeypatch):
    monkeypatch.setattr(main, "COGNITO_ISSUER", ISSUER)
    monkeypatch.setattr(main, "COGNITO_CLIENT_ID", CLIENT_ID)
    monkeypatch.setattr(main, "get_jwks_signing_key", lambda token: PUBLIC_KEY)


def make_token(**overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "sub": "verified-student",
        "client_id": CLIENT_ID,
        "token_use": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": "test-key"})


def auth_headers(subject="verified-student", **claims):
    return {"Authorization": f"Bearer {make_token(sub=subject, **claims)}"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_usage_starts_at_zero():
    response = client.get(
        "/usage/new-student",
        headers=auth_headers(subject="new-student"),
    )
    assert response.status_code == 200
    assert response.json()["user"] == "new-student"
    assert response.json()["request_count"] == 0


def test_protected_routes_reject_missing_tokens():
    assert client.post("/chat", json={"message": "hello"}).status_code == 401
    assert client.get("/usage/verified-student").status_code == 401
    assert client.post("/generate", data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate"}).status_code == 401


def test_generate_accepts_valid_access_token(monkeypatch):
    monkeypatch.setattr(
        main,
        "model_text",
        lambda prompt: '[{"question":"What does ECS manage?","answer":"ECS manages container tasks."}]',
    )
    response = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate", "count": "5"},
        headers=auth_headers(subject="flashcard-student"),
    )
    assert response.status_code == 200
    assert response.json()["cards"][0]["question"] == "What does ECS manage?"


def test_missing_cognito_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(main, "COGNITO_ISSUER", "")
    response = client.get("/usage/verified-student", headers=auth_headers())
    assert response.status_code == 503


def test_access_token_rejects_wrong_issuer():
    response = client.get(
        "/usage/verified-student",
        headers=auth_headers(iss="https://wrong-issuer.example"),
    )
    assert response.status_code == 401


def test_access_token_rejects_expired_token():
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    response = client.get(
        "/usage/verified-student",
        headers=auth_headers(exp=expired),
    )
    assert response.status_code == 401


def test_access_token_rejects_id_token_type():
    response = client.get(
        "/usage/verified-student",
        headers=auth_headers(token_use="id"),
    )
    assert response.status_code == 401


def test_access_token_rejects_another_app_client():
    response = client.get(
        "/usage/verified-student",
        headers=auth_headers(client_id="another-client"),
    )
    assert response.status_code == 401


def test_access_token_rejects_malformed_token():
    response = client.get(
        "/usage/verified-student",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


def test_access_token_rejects_invalid_signature():
    other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {
            "iss": ISSUER,
            "sub": "verified-student",
            "client_id": CLIENT_ID,
            "token_use": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        other_private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    response = client.get(
        "/usage/verified-student",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_access_token_rejects_non_rs256_algorithm():
    token = jwt.encode(
        {
            "iss": ISSUER,
            "sub": "verified-student",
            "client_id": CLIENT_ID,
            "token_use": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "test-secret-that-is-long-enough-for-hs256",
        algorithm="HS256",
        headers={"kid": "test-key"},
    )
    response = client.get(
        "/usage/verified-student",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_usage_cannot_read_another_users_counters():
    response = client.get(
        "/usage/another-student",
        headers=auth_headers(),
    )
    assert response.status_code == 403


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
    result = client.post(
        "/chat",
        json={"user": "untrusted-user", "message": "Say hello"},
        headers=auth_headers(subject="test-student"),
    )
    assert result.status_code == 200
    assert result.json()["reply"] == "Hello!"
    assert result.json()["usage"]["total_tokens"] == 5
    usage = client.get(
        "/usage/test-student",
        headers=auth_headers(subject="test-student"),
    ).json()
    assert usage["request_count"] >= 1
    assert usage["prompt_tokens"] >= 3
    assert client.get("/usage/untrusted-user", headers=auth_headers(subject="test-student")).status_code == 403


def test_chat_reports_model_unreachable(monkeypatch):
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(main.httpx, "post", fake_post)
    response = client.post("/chat", json={"message": "hello"}, headers=auth_headers())
    assert response.status_code == 502
    assert "model unreachable" in response.json()["detail"]


def test_chat_rejects_invalid_model_response(monkeypatch):
    def fake_post(url, json, timeout):
        return httpx.Response(200, json={"choices": []}, request=httpx.Request("POST", url))

    monkeypatch.setattr(main.httpx, "post", fake_post)
    response = client.post("/chat", json={"message": "hello"}, headers=auth_headers())
    assert response.status_code == 502
    assert response.json()["detail"] == "invalid model response"
