#!/usr/bin/env python3
"""
Energy Use Prediction API Demo

This script demonstrates real-world usage scenarios for the Energy Use Prediction API.
It serves as both a demo and a reference for integrating with the API.

Usage:
    python demo.py

Make sure the API is running on localhost:8000 before running this demo.
"""

from typing import Any

import requests


class EnergyAPIDemo:
    """Demo client for the Energy Use Prediction API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def check_health(self) -> dict[str, Any]:
        """Check if the API is healthy and ready."""
        print("Checking API health...")
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()

        health_data = response.json()
        print("API is healthy!")
        print(f"   Model: {health_data['model']}")
        print(f"   Version: {health_data['version']}")
        print(f"   Artifact: {health_data['artifact']}")
        return health_data

    def predict_single_building(self, building_data: dict[str, Any]) -> dict[str, Any]:
        """Make a prediction for a single building."""
        response = self.session.post(f"{self.base_url}/predict-energy-eui", json=building_data)
        response.raise_for_status()
        return response.json()

    def predict_building_portfolio(self, buildings: list[dict[str, Any]]) -> dict[str, Any]:
        """Make predictions for multiple buildings."""
        portfolio_data = {"items": buildings}
        response = self.session.post(f"{self.base_url}/predict-energy-eui/batch", json=portfolio_data)
        response.raise_for_status()
        return response.json()

    def demo_small_office(self) -> None:
        """Demo: Small office building prediction."""
        print("\nDemo 1: Small Office Building")
        print("Scenario: 3-story downtown office, 25,000 sq ft, built in 2010")

        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2010,
            "NumberofBuildings": 1,
            "NumberofFloors": 3,
            "PropertyGFATotal": 25000,
            "ENERGYSTARScore": 80,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        result = self.predict_single_building(building_data)
        prediction = result["predicted_source_eui_wn_kbtu_sf"]
        inference_time = result["inference_ms"]

        print(f"Predicted Energy Use: {prediction:.1f} kBtu/sf")
        print(f"Inference Time: {inference_time}ms")
        print(f"Request ID: {result['request_id']}")

    def demo_retail_complex(self) -> None:
        """Demo: Large retail complex prediction."""
        print("\nDemo 2: Large Retail Complex")
        print("Scenario: 2-story shopping center, 150,000 sq ft, built in 1995")

        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Retail Store",
            "YearBuilt": 1995,
            "NumberofBuildings": 1,
            "NumberofFloors": 2,
            "PropertyGFATotal": 150000,
            "ENERGYSTARScore": 65,
            "LargestPropertyUseType": "Retail Store",
            "Neighborhood": "Suburban",
        }

        result = self.predict_single_building(building_data)
        prediction = result["predicted_source_eui_wn_kbtu_sf"]

        print(f"Predicted Energy Use: {prediction:.1f} kBtu/sf")
        print("Note: Retail buildings typically have higher energy use due to lighting and HVAC needs")

    def demo_green_building(self) -> None:
        """Demo: High-efficiency green building."""
        print("\nDemo 3: High-Efficiency Green Building")
        print("Scenario: Modern 8-story office, 100,000 sq ft, built in 2020, ENERGY STAR 95")

        building_data = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2020,
            "NumberofBuildings": 1,
            "NumberofFloors": 8,
            "PropertyGFATotal": 100000,
            "ENERGYSTARScore": 95,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Downtown",
        }

        result = self.predict_single_building(building_data)
        prediction = result["predicted_source_eui_wn_kbtu_sf"]

        print(f"Predicted Energy Use: {prediction:.1f} kBtu/sf")
        print("Note: High ENERGY STAR score should result in lower energy use")

    def demo_building_portfolio(self) -> None:
        """Demo: Portfolio analysis with batch prediction."""
        print("\nDemo 4: Building Portfolio Analysis")
        print("Scenario: Property management company analyzing diverse portfolio")

        portfolio = [
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

        result = self.predict_building_portfolio(portfolio)
        results = result["results"]
        total_time = result["inference_ms"]

        print("Portfolio Analysis Results:")
        building_types = ["Office Building", "Retail Store", "Warehouse"]

        for i, (building_type, prediction_result) in enumerate(zip(building_types, results, strict=False)):
            prediction = prediction_result["predicted_source_eui_wn_kbtu_sf"]
            print(f"   {i+1}. {building_type}: {prediction:.1f} kBtu/sf")

        print(f"Total Analysis Time: {total_time}ms")
        print("Insight: Warehouse has lowest energy intensity, retail highest")

    def demo_edge_cases(self) -> None:
        """Demo: Edge cases and data validation."""
        print("\nDemo 5: Edge Cases")

        # Very old building
        print("Testing very old building (1920)...")
        old_building = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 1920,
            "NumberofBuildings": 1,
            "NumberofFloors": 6,
            "PropertyGFATotal": 35000,
            "ENERGYSTARScore": 40,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Historic District",
        }

        result = self.predict_single_building(old_building)
        prediction = result["predicted_source_eui_wn_kbtu_sf"]
        print(f"Historic Building (1920): {prediction:.1f} kBtu/sf")

        # Very large building
        print("Testing very large building (500,000 sq ft)...")
        large_building = {
            "BuildingType": "Commercial",
            "PrimaryPropertyType": "Office",
            "YearBuilt": 2015,
            "NumberofBuildings": 1,
            "NumberofFloors": 20,
            "PropertyGFATotal": 500000,
            "ENERGYSTARScore": 80,
            "LargestPropertyUseType": "Office",
            "Neighborhood": "Business District",
        }

        result = self.predict_single_building(large_building)
        prediction = result["predicted_source_eui_wn_kbtu_sf"]
        print(f"Large Building (500k sq ft): {prediction:.1f} kBtu/sf")
        print("Note: Large buildings may benefit from economies of scale")

    def run_complete_demo(self) -> None:
        """Run the complete demo sequence."""
        print("Energy Use Prediction API Demo")
        print("=" * 50)

        try:
            # Health check
            self.check_health()

            # Individual building demos
            self.demo_small_office()
            self.demo_retail_complex()
            self.demo_green_building()

            # Portfolio demo
            self.demo_building_portfolio()

            # Edge cases
            self.demo_edge_cases()

            print("\nDemo completed successfully!")
            print("\nKey Takeaways:")
            print("• The API provides fast, reliable energy use predictions")
            print("• Building type, age, and efficiency ratings significantly impact predictions")
            print("• Batch processing enables efficient portfolio analysis")
            print("• The API handles edge cases gracefully")
            print("\nIntegration Guide:")
            print("• Use /health to check API availability")
            print("• Use /predict-energy-eui for single building predictions")
            print("• Use /predict-energy-eui/batch for portfolio analysis")
            print("• All predictions include request IDs for tracking")

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to API")
            print("Make sure the API is running on http://localhost:8000")
            print("Run: docker-compose up -d")
        except requests.exceptions.HTTPError as e:
            print(f"API Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def main() -> None:
    """Run the demo."""
    demo = EnergyAPIDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()
