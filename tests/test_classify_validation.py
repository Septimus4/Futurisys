from __future__ import annotations

from fastapi.testclient import TestClient


def test_classify_validation_bad_text(client: TestClient) -> None:
    payload = {
        "text": "   ",
        "candidate_labels": ["a", "b"],
    }
    r = client.post("/classify", json=payload)
    assert r.status_code == 422

def test_classify_validation_labels(client: TestClient) -> None:
    payload = {
        "text": "hello",
        "candidate_labels": ["onlyone"],
    }
    r = client.post("/classify", json=payload)
    assert r.status_code == 422
