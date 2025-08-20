"""Test health endpoint."""

import uuid

from fastapi.testclient import TestClient


def test_health_endpoint_success(client: TestClient) -> None:
    """Test health endpoint returns correct response."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "model" in data
    assert "artifact" in data
    assert "version" in data
    assert data["model"] == "sklearn-random-forest"


def test_health_endpoint_has_request_id(client: TestClient) -> None:
    """Test health endpoint includes request ID in headers."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    # Verify it's a valid UUID format
    request_id = response.headers["X-Request-ID"]

    uuid.UUID(request_id)  # Will raise ValueError if invalid
