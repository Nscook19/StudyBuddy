"""Milestone 3 flashcard generation tests with mocked model completions."""

import io
import json
import re

import httpx
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app import main

client = TestClient(main.app)


def card_array(count):
    return json.dumps([
        {
            "question": f"What is cloud concept {index}?",
            "answer": f"Cloud concept {index} is a study topic.",
        }
        for index in range(1, count + 1)
    ])


def setup_fake(monkeypatch, response=None):
    calls = []

    def fake_model(prompt):
        calls.append(prompt)
        if response is not None:
            return response
        count = int(re.search(r"exactly (\d+) cards", prompt).group(1))
        return card_array(count)

    monkeypatch.setattr(main, "model_text", fake_model)
    return calls


def test_ai_recommended_target_uses_source_length_and_one_model_request(monkeypatch):
    source = "Cloud computing fundamentals. " * 101
    calls = setup_fake(monkeypatch)
    response = client.post(
        "/generate",
        data={"mode": "notes", "notes": source},
    )

    assert response.status_code == 200, response.text
    assert response.json()["count"] == 7
    assert response.json()["recommended"]
    assert response.json()["requested_count"] is None
    assert len(calls) == 1
    assert "exactly 7 cards" in calls[0]
    assert "only the supplied material" in calls[0]
    assert "concise, factual" in calls[0]
    assert "JSON array" in calls[0]
    assert "no markdown" in calls[0]


def test_ai_recommended_target_is_capped_and_source_is_truncated(monkeypatch):
    source = "x" * (main.MAX_SOURCE_CHARS + 500)
    calls = setup_fake(monkeypatch)
    response = client.post(
        "/generate",
        data={"mode": "notes", "notes": source},
    )

    assert response.status_code == 200, response.text
    assert response.json()["count"] == main.MAX_CARDS
    assert len(calls) == 1
    supplied_source = calls[0].split("STUDY MATERIAL:\n", 1)[1]
    assert len(supplied_source) == main.MAX_SOURCE_CHARS
    assert "exactly 20 cards" in calls[0]


def test_manual_count_is_a_target_and_fewer_cards_are_accepted(monkeypatch):
    cards = json.dumps([
        {"question": "What does ECS orchestrate?", "answer": "ECS coordinates container tasks."},
        {"question": "What is Fargate?", "answer": "Fargate runs containers without managing servers."},
    ])
    calls = setup_fake(monkeypatch, cards)
    response = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate", "count": "20"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["count"] == 2
    assert response.json()["requested_count"] == 20
    assert response.json()["message"] == "Generated 2 of 20 requested cards."
    assert len(calls) == 1
    assert "exactly 20 cards" in calls[0]
    assert "established facts about the topic" in calls[0]


def test_generation_discards_only_case_insensitive_exact_question_duplicates(monkeypatch):
    completion = json.dumps([
        {"question": "What is ECS?", "answer": "ECS manages container tasks."},
        {"question": " what IS ecs? ", "answer": "Duplicate question."},
        {"question": "What does ECS orchestrate?", "answer": "ECS manages container tasks."},
    ])
    calls = setup_fake(monkeypatch, completion)
    cards = main.generate_cards("Amazon ECS and Fargate.", 5, from_topic=True)

    assert len(cards) == 2
    assert cards[0]["question"] == "What is ECS?"
    assert cards[1]["question"] == "What does ECS orchestrate?"
    assert cards[0]["answer"] == cards[1]["answer"]
    assert len(calls) == 1


def test_card_validation_keeps_valid_cards_and_rejects_bad_lengths():
    cards = main.parse_cards(json.dumps([
        {"question": "What is valid?", "answer": "A valid answer."},
        {"question": " ", "answer": "Missing question."},
        {"question": "A" * 241, "answer": "Too long question."},
        {"question": "What has a long answer?", "answer": "A" * 401},
        "not a card",
    ]))

    assert cards == [{"question": "What is valid?", "answer": "A valid answer."}]


def test_markdown_wrapped_json_is_rejected(monkeypatch):
    calls = setup_fake(monkeypatch, "```json\n[]\n```")
    response = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate", "count": "5"},
    )

    assert response.status_code == 502
    assert "invalid flashcard data" in response.json()["detail"]
    assert len(calls) == 1


def test_no_usable_cards_returns_clear_error(monkeypatch):
    calls = setup_fake(monkeypatch, json.dumps([
        {"question": "", "answer": "Not usable."},
        {"question": "What is a card?", "answer": ""},
    ]))
    response = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate", "count": "5"},
    )

    assert response.status_code == 502
    assert "could not produce usable flashcards" in response.json()["detail"]
    assert len(calls) == 1


def test_bad_count_and_empty_source_are_rejected():
    bad_count = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Docker Compose explained", "count": "15"},
    )
    empty_source = client.post(
        "/generate",
        data={"mode": "topic", "topic": "hi", "count": "10"},
    )

    assert bad_count.status_code == 422
    assert empty_source.status_code == 400


def test_non_pdf_upload_rejected():
    response = client.post(
        "/generate",
        data={"mode": "pdf", "count": "10"},
        files={"file": ("notes.pdf", b"not pdf", "application/pdf")},
    )
    assert response.status_code == 400


def test_pdf_without_extractable_text_is_clear_error():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    result = io.BytesIO()
    writer.write(result)
    response = client.post(
        "/generate",
        data={"mode": "pdf", "count": "10"},
        files={"file": ("empty.pdf", result.getvalue(), "application/pdf")},
    )

    assert response.status_code == 400
    assert "selectable text" in response.json()["detail"]


def test_too_large_pdf_rejected():
    response = client.post(
        "/generate",
        data={"mode": "pdf", "count": "10"},
        files={"file": ("notes.pdf", b"%PDF-" + b"x" * (main.MAX_PDF_BYTES + 1), "application/pdf")},
    )
    assert response.status_code == 413


def test_pdf_over_page_limit_rejected():
    writer = PdfWriter()
    for _ in range(main.MAX_PAGES + 1):
        writer.add_blank_page(width=612, height=792)
    result = io.BytesIO()
    writer.write(result)
    response = client.post(
        "/generate",
        data={"mode": "pdf", "count": "10"},
        files={"file": ("long.pdf", result.getvalue(), "application/pdf")},
    )

    assert response.status_code == 400
    assert "30 pages or fewer" in response.json()["detail"]


def test_model_connection_error_is_distinct(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(main.httpx, "post", fail)
    response = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate", "count": "5"},
    )

    assert response.status_code == 502
    assert "connect" in response.json()["detail"].lower()


def test_model_timeout_is_distinct(monkeypatch):
    def fail(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(main.httpx, "post", fail)
    response = client.post(
        "/generate",
        data={"mode": "topic", "topic": "Amazon ECS and AWS Fargate", "count": "5"},
    )

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]
