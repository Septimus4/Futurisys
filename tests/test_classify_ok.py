from __future__ import annotations

from fastapi.testclient import TestClient


def test_classify_ok(client: TestClient) -> None:
    payload = {
        "text": "I love writing Python and deploying models.",
        "candidate_labels": ["technology", "sports"],
        "multi_label": False,
    }
    r = client.post("/classify", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data.keys()) == {"request_id", "labels", "scores", "top_label", "inference_ms"}
    labels_len = len(data["labels"])  # allow for potential extra label ordering
    cand_len = len(payload["candidate_labels"])
    assert labels_len in {cand_len, cand_len + 1}
