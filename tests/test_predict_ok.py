"""Test successful prediction scenarios."""

import uuid

from fastapi.testclient import TestClient


def test_predict_single_success(client: TestClient, sample_prediction_request) -> None:
    """Test successful single prediction."""
    response = client.post("/predict-energy-eui", json=sample_prediction_request)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "request_id" in data
    assert "predicted_source_eui_wn_kbtu_sf" in data
    assert "model_name" in data
    assert "model_version" in data
    assert "inference_ms" in data

    # Verify types and reasonable values
    uuid.UUID(data["request_id"])  # Should be valid UUID
    assert isinstance(data["predicted_source_eui_wn_kbtu_sf"], int | float)
    assert data["predicted_source_eui_wn_kbtu_sf"] > 0  # Energy should be positive
    assert data["model_name"] == "sklearn-random-forest"
    assert isinstance(data["inference_ms"], int)
    assert data["inference_ms"] >= 0


def test_predict_single_different_inputs(client: TestClient) -> None:
    """Test prediction with different input combinations."""
    test_cases = [
        # Case 1: Small building
        {
            "ENERGYSTARScore": 90,
            "NumberofBuildings": 1,
            "NumberofFloors": 2,
            "PropertyGFATotal": 5000,
            "YearBuilt": 2020,
            "BuildingType": "Residential",
            "PrimaryPropertyType": "Multifamily",
            "LargestPropertyUseType": "Multifamily",
            "Neighborhood": "BALLARD",
        },
        # Case 2: Large building
        {
            "ENERGYSTARScore": 50,
            "NumberofBuildings": 1,
            "NumberofFloors": 40,
            "PropertyGFATotal": 1000000,
            "YearBuilt": 1980,
            "BuildingType": "NonResidential",
            "PrimaryPropertyType": "Office",
            "LargestPropertyUseType": "Office",
            "Neighborhood": "SOUTH LAKE UNION",
        },
    ]

    for i, test_case in enumerate(test_cases):
        response = client.post("/predict-energy-eui", json=test_case)
        assert response.status_code == 200, f"Test case {i+1} failed"

        data = response.json()
        assert isinstance(data["predicted_source_eui_wn_kbtu_sf"], int | float)
        assert data["predicted_source_eui_wn_kbtu_sf"] > 0


def test_predict_missing_energy_star_score(client: TestClient, sample_prediction_request) -> None:
    """Test prediction without ENERGYSTARScore (optional field)."""
    request_data = sample_prediction_request.copy()
    del request_data["ENERGYSTARScore"]

    response = client.post("/predict-energy-eui", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data["predicted_source_eui_wn_kbtu_sf"], int | float)


def test_predict_batch_success(client: TestClient, sample_batch_request) -> None:
    """Test successful batch prediction."""
    response = client.post("/predict-energy-eui/batch", json=sample_batch_request)

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "request_id" in data
    assert "results" in data
    assert "inference_ms" in data

    # Verify request ID
    uuid.UUID(data["request_id"])

    # Verify results
    results = data["results"]
    assert len(results) == len(sample_batch_request["items"])

    for i, result in enumerate(results):
        assert result["index"] == i
        assert isinstance(result["predicted_source_eui_wn_kbtu_sf"], int | float)
        assert result["predicted_source_eui_wn_kbtu_sf"] > 0

    # Verify timing
    assert isinstance(data["inference_ms"], int)
    assert data["inference_ms"] >= 0


def test_predict_batch_single_item(client: TestClient, sample_prediction_request) -> None:
    """Test batch prediction with single item."""
    batch_request = {"items": [sample_prediction_request]}

    response = client.post("/predict-energy-eui/batch", json=batch_request)
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["index"] == 0


def test_request_persistence(client: TestClient, sample_prediction_request) -> None:
    """Test that requests are persisted and can be looked up."""
    # Make a prediction
    response = client.post("/predict-energy-eui", json=sample_prediction_request)
    assert response.status_code == 200

    request_id = response.json()["request_id"]

    # Look up the request
    lookup_response = client.get(f"/requests/{request_id}")
    assert lookup_response.status_code == 200

    lookup_data = lookup_response.json()
    assert lookup_data["request_id"] == request_id
    assert "received_at" in lookup_data
    assert "features" in lookup_data
    assert lookup_data["result"] is not None
    assert lookup_data["error"] is None

    # Verify the stored features match the original request
    stored_features = lookup_data["features"]
    for key, value in sample_prediction_request.items():
        assert stored_features[key] == value
