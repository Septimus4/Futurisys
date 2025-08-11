from __future__ import annotations

from sqlalchemy import select
from src.models import InferenceRequest, InferenceResult

def test_persistence(client):
    payload = {"text": "Persistence test", "candidate_labels": ["tech", "sports"], "multi_label": False}
    r = client.post("/classify", json=payload)
    assert r.status_code == 200
    request_id = r.json()["request_id"]

    # fetch stored request via API
    r2 = client.get(f"/requests/{request_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["request"]["id"] == request_id
    assert data["result"] is not None
