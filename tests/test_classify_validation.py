from __future__ import annotations

def test_classify_validation_bad_text(client):
    payload = {
        "text": "   ",
        "candidate_labels": ["a", "b"],
    }
    r = client.post("/classify", json=payload)
    assert r.status_code == 422

def test_classify_validation_labels(client):
    payload = {
        "text": "hello",
        "candidate_labels": ["onlyone"],
    }
    r = client.post("/classify", json=payload)
    assert r.status_code == 422
