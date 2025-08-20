"""Model runtime loader and prediction service."""

import json
import time
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from .settings import settings


class ModelRuntime:
    """Runtime loader and predictor for the energy use prediction model."""

    def __init__(self) -> None:
        """Initialize the model runtime."""
        self._pipeline: Pipeline | None = None
        self._model_metadata: dict[str, Any] | None = None
        self._is_loaded = False

    def load_artifacts(self) -> None:
        """Load the model artifacts from disk."""
        # Load the trained pipeline
        artifact_path = settings.get_model_artifact_path()
        if not artifact_path.exists():
            raise FileNotFoundError(f"Model artifact not found: {artifact_path}")

        print(f"Loading model from {artifact_path}")
        self._pipeline = joblib.load(artifact_path)

        # Load model metadata
        card_path = settings.get_model_card_path()
        if card_path.exists():
            with open(card_path) as f:
                self._model_metadata = json.load(f)
        else:
            # Fallback metadata if model card is missing
            self._model_metadata = {
                "model_name": settings.model_name,
                "model_version": settings.model_version,
                "artifact_path": str(artifact_path),
            }

        self._is_loaded = True
        print(f"Model loaded successfully: {self.get_model_name()} v{self.get_model_version()}")

    def is_ready(self) -> bool:
        """Check if the model is loaded and ready for predictions."""
        return self._is_loaded and self._pipeline is not None

    def get_model_name(self) -> str:
        """Get the model name."""
        if self._model_metadata:
            return self._model_metadata.get("model_name", settings.model_name)
        return settings.model_name

    def get_model_version(self) -> str:
        """Get the model version."""
        if self._model_metadata:
            return self._model_metadata.get("model_version", settings.model_version)
        return settings.model_version

    def get_artifact_path(self) -> str:
        """Get the model artifact path."""
        if self._model_metadata:
            return self._model_metadata.get("artifact_path", settings.model_artifact_path)
        return settings.model_artifact_path

    def get_feature_names(self) -> list[str]:
        """Get the expected feature names."""
        if self._model_metadata and "feature_contract" in self._model_metadata:
            contract = self._model_metadata["feature_contract"]
            return contract.get("numeric", []) + contract.get("categorical", [])

        # Fallback to hardcoded feature names
        return [
            "ENERGYSTARScore",
            "NumberofBuildings",
            "NumberofFloors",
            "PropertyGFATotal",
            "YearBuilt",
            "BuildingType",
            "PrimaryPropertyType",
            "LargestPropertyUseType",
            "Neighborhood",
        ]

    def _prepare_features(self, features: dict[str, Any]) -> pd.DataFrame:
        """Prepare features for prediction."""
        if not self.is_ready():
            raise RuntimeError("Model is not loaded")

        # Get expected feature names
        expected_features = self.get_feature_names()

        # Create DataFrame with the expected columns
        df = pd.DataFrame([features])

        # Ensure all expected columns are present
        for col in expected_features:
            if col not in df.columns:
                df[col] = None

        # Select only the expected columns in the correct order
        df = df[expected_features]

        return df

    def predict_one(self, features: dict[str, Any]) -> tuple[float, int]:
        """
        Make a single prediction.

        Args:
            features: Dictionary of input features

        Returns:
            Tuple of (prediction, inference_time_ms)
        """
        if not self.is_ready():
            raise RuntimeError("Model is not loaded")

        start_time = time.time()

        # Prepare features
        df = self._prepare_features(features)

        # Make prediction
        prediction = self._pipeline.predict(df)[0]

        end_time = time.time()
        inference_ms = int((end_time - start_time) * 1000)

        return float(prediction), inference_ms

    def predict_batch(self, features_list: list[dict[str, Any]]) -> tuple[list[float], int]:
        """
        Make batch predictions.

        Args:
            features_list: List of feature dictionaries

        Returns:
            Tuple of (predictions_list, total_inference_time_ms)
        """
        if not self.is_ready():
            raise RuntimeError("Model is not loaded")

        if not features_list:
            return [], 0

        start_time = time.time()

        # Prepare all features
        expected_features = self.get_feature_names()
        df = pd.DataFrame(features_list)

        # Ensure all expected columns are present
        for col in expected_features:
            if col not in df.columns:
                df[col] = None

        # Select only the expected columns in the correct order
        df = df[expected_features]

        # Make predictions
        predictions = self._pipeline.predict(df)

        end_time = time.time()
        inference_ms = int((end_time - start_time) * 1000)

        return predictions.tolist(), inference_ms


# Global model runtime instance
model_runtime = ModelRuntime()
