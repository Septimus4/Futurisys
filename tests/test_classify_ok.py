from __future__ import annotations

def test_classify_ok(client):
    payload = {
        "text": "I love writing Python and deploying models.",
        "candidate_labels": ["technology", "sports"],
        "multi_label": False,
    }
    r = client.post("/classify", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data.keys()) == {"request_id", "labels", "scores", "top_label", "inference_ms"}
    assert len(data["labels"]) == len(payload["candidate_labels"]) or len(data["labels"]) == len(payload["candidate_labels"]) + 1
