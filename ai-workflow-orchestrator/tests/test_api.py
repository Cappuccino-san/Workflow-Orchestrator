"""Smoke tests for the FastAPI surface."""

from fastapi.testclient import TestClient

from workflow_orchestrator.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage_endpoint_returns_structured_result():
    response = client.post(
        "/triage",
        json={
            "id": "T-99",
            "source": "ticket",
            "subject": "Invoice overcharged",
            "text": "I was overcharged on my invoice and need a refund.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["item_id"] == "T-99"
    assert body["classification"]["category"] == "billing"
    assert body["decision"]["priority"] in {"P1", "P2", "P3", "P4"}
