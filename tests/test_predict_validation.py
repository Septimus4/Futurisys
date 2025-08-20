"""Test input validation and error cases."""

import uuid

from fastapi.testclient import TestClient


def test_predict_missing_required_field(client: TestClient, sample_prediction_request: dict) -> None:
    """Test prediction with missing required field."""
    request_data = sample_prediction_request.copy()
    del request_data["NumberofBuildings"]

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422  # Validation error


def test_predict_invalid_energy_star_score(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with invalid ENERGYSTARScore."""
    # Test negative value
    request_data = sample_prediction_request.copy()
    request_data["ENERGYSTARScore"] = -10

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422

    # Test value over 100
    request_data["ENERGYSTARScore"] = 150
    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_invalid_number_of_buildings(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with invalid NumberofBuildings."""
    request_data = sample_prediction_request.copy()
    request_data["NumberofBuildings"] = 0

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_invalid_number_of_floors(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with invalid NumberofFloors."""
    request_data = sample_prediction_request.copy()
    request_data["NumberofFloors"] = -1

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_invalid_property_gfa_total(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with invalid PropertyGFATotal."""
    request_data = sample_prediction_request.copy()
    request_data["PropertyGFATotal"] = 0

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_invalid_year_built(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with invalid YearBuilt."""
    # Test year too old
    request_data = sample_prediction_request.copy()
    request_data["YearBuilt"] = 1700

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422

    # Test future year
    request_data["YearBuilt"] = 2030
    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_empty_categorical_field(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with empty categorical field."""
    request_data = sample_prediction_request.copy()
    request_data["BuildingType"] = ""

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_whitespace_only_categorical_field(
    client: TestClient,
    sample_prediction_request: dict,
) -> None:
    """Test prediction with whitespace-only categorical field."""
    request_data = sample_prediction_request.copy()
    request_data["BuildingType"] = "   "

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_extra_fields_rejected(client: TestClient, sample_prediction_request) -> None:
    """Test that extra fields are rejected."""
    request_data = sample_prediction_request.copy()
    request_data["extra_field"] = "should_be_rejected"

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_wrong_field_types(client: TestClient, sample_prediction_request) -> None:
    """Test prediction with wrong field types."""
    # String instead of number
    request_data = sample_prediction_request.copy()
    request_data["NumberofBuildings"] = "not_a_number"

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 422


def test_predict_batch_empty_items(client: TestClient) -> None:
    """Test batch prediction with empty items list."""
    response = client.post("/predict-energy-eui/batch", json={"items": []})
    assert response.status_code == 422


def test_predict_batch_too_many_items(client: TestClient, sample_prediction_request) -> None:
    """Test batch prediction with too many items."""
    # Create a batch that exceeds the limit
    large_batch = {"items": [sample_prediction_request] * 600}  # Over the 512 limit

    response = client.post("/predict-energy-eui/batch", json=large_batch)
    assert response.status_code == 422  # Pydantic validation error


def test_predict_batch_invalid_item(client: TestClient, sample_prediction_request) -> None:
    """Test batch prediction with one invalid item."""
    invalid_item = sample_prediction_request.copy()
    invalid_item["NumberofBuildings"] = -1

    batch_request = {"items": [sample_prediction_request, invalid_item]}

    response = client.post("/predict-energy-eui/batch", json=batch_request)
    assert response.status_code == 422


def test_predict_batch_extra_fields_rejected(client: TestClient, sample_prediction_request) -> None:
    """Test that extra fields in batch request are rejected."""
    batch_request = {
        "items": [sample_prediction_request],
        "extra_field": "should_be_rejected",
    }

    response = client.post("/predict-energy-eui/batch", json=batch_request)
    assert response.status_code == 422


def test_request_lookup_invalid_uuid(client: TestClient) -> None:
    """Test request lookup with invalid UUID."""
    response = client.get("/requests/not-a-uuid")
    assert response.status_code == 422


def test_request_lookup_nonexistent_request(client: TestClient) -> None:
    """Test request lookup for nonexistent request."""
    fake_id = str(uuid.uuid4())

    response = client.get(f"/requests/{fake_id}")
    assert response.status_code == 404
