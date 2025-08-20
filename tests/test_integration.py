"""Integration tests for the Energy Use Prediction API.

These tests demonstrate real-world usage scenarios and serve as:
1. Demo examples for API usage
2. Regression tests to catch breaking changes
3. End-to-end validation of the complete system

The tests use realistic building data and validate the complete request/response cycle.
"""

from fastapi.testclient import TestClient


class TestEnergyPredictionIntegration:
    """Integration tests for energy use prediction scenarios."""

    def test_small_office_building_prediction(self, client: TestClient) -> None:
        """Test prediction for a typical small office building.

        Scenario: Small downtown office building built in 2010.
        This represents a common modern office building type.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2010,
            "NumberofBuildings": 1,
            "NumberofFloors": 3,
            "PropertyGFATotal": 25000,  # 25,000 sq ft
            "ENERGYSTARScore": 80,  # Good energy efficiency
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "request_id" in data
        assert "predicted_source_eui_wn_kbtu_sf" in data
        assert "model_name" in data
        assert "model_version" in data
        assert "inference_ms" in data

        # Validate prediction reasonableness for small office
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 120.0 <= prediction <= 150.0, f"Prediction {prediction} seems unrealistic for small office"

        # Validate model metadata
        assert data["model_name"] == "sklearn-random-forest"
        assert data["model_version"] == "20250819_rf_v1"
        assert isinstance(data["inference_ms"], int | float)
        assert data["inference_ms"] > 0

    def test_large_retail_complex_prediction(self, client: TestClient) -> None:
        """Test prediction for a large retail complex.

        Scenario: Large shopping center with multiple floors.
        This represents a high-energy-use commercial building.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Retail Store",
            "YearBuilt": 1995,
            "NumberofBuildings": 1,
            "NumberofFloors": 2,
            "PropertyGFATotal": 150000,  # 150,000 sq ft - large retail
            "ENERGYSTARScore": 65,  # Average energy efficiency
            "LargestPropertyUseType": "Retail Store",
            "Neighborhood": "Suburban",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Validate prediction reasonableness for large retail
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 150.0 <= prediction <= 200.0, f"Prediction {prediction} seems unrealistic for retail complex"

    def test_older_warehouse_prediction(self, client: TestClient) -> None:
        """Test prediction for an older warehouse building.

        Scenario: Industrial warehouse from the 1980s.
        This represents lower energy intensity industrial use.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Warehouse",
            "YearBuilt": 1985,
            "NumberofBuildings": 1,
            "NumberofFloors": 1,
            "PropertyGFATotal": 80000,  # 80,000 sq ft warehouse
            "ENERGYSTARScore": 50,  # Below average efficiency (older building)
            "LargestPropertyUseType": "Warehouse",
            "Neighborhood": "Industrial",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Validate prediction reasonableness for warehouse
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 125.0 <= prediction <= 150.0, f"Prediction {prediction} seems unrealistic for warehouse"

    def test_high_efficiency_new_building(self, client: TestClient) -> None:
        """Test prediction for a new, highly efficient building.

        Scenario: Modern green office building with excellent energy performance.
        This tests the model's response to high-efficiency buildings.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2020,
            "NumberofBuildings": 1,
            "NumberofFloors": 8,
            "PropertyGFATotal": 100000,  # 100,000 sq ft modern office
            "ENERGYSTARScore": 95,  # Excellent energy efficiency
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # High efficiency buildings should have lower EUI predictions
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 110.0 <= prediction <= 135.0, f"Prediction {prediction} seems unrealistic for high-efficiency building"

    def test_mixed_use_building_prediction(self, client: TestClient) -> None:
        """Test prediction for a mixed-use building.

        Scenario: Building with mixed commercial uses.
        This tests the model's handling of diverse property types.
        """
        building_data = {
            "BuildingType": "Mixed Use",
            "PrimaryPropertyType": "Mixed Use Property",
            "YearBuilt": 2005,
            "NumberofBuildings": 1,
            "NumberofFloors": 5,
            "PropertyGFATotal": 60000,  # 60,000 sq ft mixed use
            "ENERGYSTARScore": 70,  # Good efficiency
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Urban",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Validate prediction for mixed use
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 190.0 <= prediction <= 220.0, f"Prediction {prediction} seems unrealistic for mixed-use building"

    def test_batch_prediction_diverse_portfolio(self, client: TestClient) -> None:
        """Test batch prediction for a diverse building portfolio.

        Scenario: Property management company evaluating multiple buildings.
        This demonstrates the batch API with realistic building mix.
        """
        portfolio = {
            "items": [
                {
                    "BuildingType": "Commercial",
                    "PrimaryPropertyType": "Office",
                    "YearBuilt": 2010,
                    "NumberofBuildings": 1,
                    "NumberofFloors": 4,
                    "PropertyGFATotal": 40000,
                    "ENERGYSTARScore": 75,
                    "LargestPropertyUseType": "Office",
                    "Neighborhood": "Downtown",
                },
                {
                    "BuildingType": "Commercial",
                    "PrimaryPropertyType": "Retail Store",
                    "YearBuilt": 2000,
                    "NumberofBuildings": 1,
                    "NumberofFloors": 1,
                    "PropertyGFATotal": 15000,
                    "ENERGYSTARScore": 60,
                    "LargestPropertyUseType": "Retail Store",
                    "Neighborhood": "Suburban",
                },
                {
                    "BuildingType": "Commercial",
                    "PrimaryPropertyType": "Warehouse",
                    "YearBuilt": 1990,
                    "NumberofBuildings": 1,
                    "NumberofFloors": 1,
                    "PropertyGFATotal": 75000,
                    "ENERGYSTARScore": 55,
                    "LargestPropertyUseType": "Warehouse",
                    "Neighborhood": "Industrial",
                },
            ]
        }

        response = client.post("/predict-energy-eui/batch", json=portfolio)

        assert response.status_code == 200
        data = response.json()

        # Validate batch response structure
        assert "request_id" in data
        assert "results" in data
        assert "inference_ms" in data

        # Validate individual predictions
        results = data["results"]
        assert len(results) == 3

        for i, result in enumerate(results):
            assert "index" in result
            assert "predicted_source_eui_wn_kbtu_sf" in result
            assert result["index"] == i

            prediction_value = result["predicted_source_eui_wn_kbtu_sf"]
            assert 110.0 <= prediction_value <= 220.0, f"Prediction {i}: {prediction_value} seems unrealistic"

    def test_edge_case_very_old_building(self, client: TestClient) -> None:
        """Test prediction for a very old building.

        Scenario: Historic building from early 1900s.
        This tests the model's handling of very old construction.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 1920,  # Very old building
            "NumberofBuildings": 1,
            "NumberofFloors": 6,
            "PropertyGFATotal": 35000,
            "ENERGYSTARScore": 40,  # Poor efficiency expected for old building
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Historic District",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Old buildings might have higher energy use
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 165.0 <= prediction <= 195.0, f"Prediction {prediction} seems unrealistic for very old building"

    def test_edge_case_very_large_building(self, client: TestClient) -> None:
        """Test prediction for a very large building.

        Scenario: Massive commercial complex or campus.
        This tests the model's handling of scale effects.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2015,
            "NumberofBuildings": 1,
            "NumberofFloors": 20,
            "PropertyGFATotal": 500000,  # Very large building
            "ENERGYSTARScore": 80,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Business District",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Large buildings might have economies of scale
        prediction = data["predicted_source_eui_wn_kbtu_sf"]
        assert 175.0 <= prediction <= 205.0, f"Prediction {prediction} seems unrealistic for very large building"

    def test_performance_regression_check(self, client: TestClient) -> None:
        """Test that API performance remains within acceptable bounds.

        This serves as a regression test for performance degradation.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2010,
            "NumberofBuildings": 1,
            "NumberofFloors": 5,
            "PropertyGFATotal": 50000,
            "ENERGYSTARScore": 75,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Performance regression check - inference should be fast
        inference_time = data["inference_ms"]
        assert inference_time < 1000, f"Inference took {inference_time}ms, which may indicate performance regression"

        # Typical inference should be much faster
        assert inference_time < 500, f"Inference took {inference_time}ms, should typically be under 500ms"

    def test_model_consistency_regression(self, client: TestClient) -> None:
        """Test that the model produces consistent predictions.

        This serves as a regression test for model drift or loading issues.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2000,
            "NumberofBuildings": 1,
            "NumberofFloors": 10,
            "PropertyGFATotal": 100000,
            "ENERGYSTARScore": 70,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        # Make the same prediction multiple times
        predictions = []
        for _ in range(3):
            response = client.post("/predict-energy-eui", json=building_data)
            assert response.status_code == 200
            data = response.json()
            predictions.append(data["predicted_source_eui_wn_kbtu_sf"])

        # All predictions should be identical (deterministic model)
        assert all(
            pred == predictions[0] for pred in predictions
        ), f"Model predictions are not consistent: {predictions}"

    def test_api_response_format_stability(self, client: TestClient) -> None:
        """Test that API response format remains stable.

        This serves as a regression test for breaking API changes.
        """
        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2010,
            "NumberofBuildings": 1,
            "NumberofFloors": 5,
            "PropertyGFATotal": 50000,
            "ENERGYSTARScore": 75,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        response = client.post("/predict-energy-eui", json=building_data)

        assert response.status_code == 200
        data = response.json()

        # Verify exact response format (breaking change detection)
        expected_keys = {
            "request_id",
            "predicted_source_eui_wn_kbtu_sf",
            "model_name",
            "model_version",
            "inference_ms",
        }

        actual_keys = set(data.keys())
        assert actual_keys == expected_keys, f"Response format changed. Expected: {expected_keys}, Got: {actual_keys}"

        # Verify data types
        assert isinstance(data["request_id"], str)
        assert isinstance(data["predicted_source_eui_wn_kbtu_sf"], int | float)
        assert isinstance(data["model_name"], str)
        assert isinstance(data["model_version"], str)
        assert isinstance(data["inference_ms"], int | float)


class TestHealthCheckIntegration:
    """Integration tests for health check endpoint."""

    def test_health_check_complete_system(self, client: TestClient) -> None:
        """Test that health check validates the complete system.

        This ensures the model is loaded and database is accessible.
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify health check response format
        expected_keys = {"status", "model", "artifact", "version"}
        actual_keys = set(data.keys())
        assert (
            actual_keys == expected_keys
        ), f"Health check format changed. Expected: {expected_keys}, Got: {actual_keys}"

        # Verify system is healthy
        assert data["status"] == "ok"
        assert data["model"] == "sklearn-random-forest"
        assert data["artifact"] == "model/energy_rf.joblib"
        assert data["version"] == "20250819_rf_v1"
