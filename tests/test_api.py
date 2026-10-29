import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "provider" in response.json()


def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "provider" in data


def test_verify_basic():
    response = client.post("/v1/verify", json={
        "text": "DeepSeek-R1 is a 14 billion parameter model.",
        "mode": "fixture",
        "top_k": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "claims" in data
    assert len(data["claims"]) > 0
    assert "verdict" in data["claims"][0]


def test_verify_empty_text():
    response = client.post("/v1/verify", json={
        "text": "",
        "mode": "fixture"
    })
    assert response.status_code == 500


def test_verify_too_long():
    long_text = "test " * 2000
    response = client.post("/v1/verify", json={
        "text": long_text,
        "mode": "fixture"
    })
    assert response.status_code == 400


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "verdict_distribution" in data


def test_fixture_provider():
    response = client.post("/v1/verify", json={
        "text": "DeepSeek-R1 is the most efficient model available.",
        "mode": "fixture"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["claims"][0]["verdict"] == "NOT_ENOUGH_EVIDENCE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
