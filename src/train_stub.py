#!/usr/bin/env python3
"""
Training script for the energy use prediction model.
Creates a RandomForestRegressor pipeline with proper preprocessing.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def create_preprocessor() -> ColumnTransformer:
    """Create the preprocessing pipeline for features."""
    numeric_features = [
        "ENERGYSTARScore",
        "NumberofBuildings",
        "NumberofFloors",
        "PropertyGFATotal",
        "YearBuilt",
    ]

    categorical_features = [
        "BuildingType",
        "PrimaryPropertyType",
        "LargestPropertyUseType",
        "Neighborhood",
    ]

    numeric_transformer = SimpleImputer(strategy="median")
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocessor


def load_and_prepare_data(csv_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load the CSV data and prepare features and target."""
    print(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)

    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # Define our features
    feature_columns = [
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

    # Target column
    target_column = "SourceEUIWN(kBtu/sf)"

    # Check if all required columns exist
    missing_cols = [col for col in [*feature_columns, target_column] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in dataset: {missing_cols}")

    # Filter data to remove rows with missing target
    df_clean = df.dropna(subset=[target_column])
    print(f"After removing rows with missing target: {df_clean.shape}")

    X = df_clean[feature_columns].copy()  # noqa: N806
    y = df_clean[target_column].copy()

    # Basic data validation
    print("Target statistics:")
    print(f"  Min: {y.min():.2f}")
    print(f"  Max: {y.max():.2f}")
    print(f"  Mean: {y.mean():.2f}")
    print(f"  Median: {y.median():.2f}")

    return X, y


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[Pipeline, dict[str, Any]]:
    """Train the RandomForest model and return pipeline with metrics."""
    print("Creating preprocessing pipeline...")
    preprocessor = create_preprocessor()

    print("Creating model pipeline...")
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    n_jobs=-1,
                    max_depth=15,
                    min_samples_split=10,
                    min_samples_leaf=4,
                ),
            ),
        ]
    )

    # Split data for evaluation
    X_train, X_test, y_train, y_test = train_test_split(  # noqa: N806
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training set size: {X_train.shape[0]}")
    print(f"Test set size: {X_test.shape[0]}")

    print("Training model...")
    pipeline.fit(X_train, y_train)

    # Evaluate model
    print("Evaluating model...")
    y_pred = pipeline.predict(X_test)

    metrics = {
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "mse": float(mean_squared_error(y_test, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "r2": float(r2_score(y_test, y_pred)),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_names": X.columns.tolist(),
        "target_name": "SourceEUIWN(kBtu/sf)",
    }

    print("Model Performance:")
    print(f"  MAE: {metrics['mae']:.2f}")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  R²: {metrics['r2']:.3f}")

    return pipeline, metrics


def save_artifacts(pipeline: Pipeline, metrics: dict[str, Any], output_dir: Path) -> None:
    """Save the trained model and metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = output_dir / "energy_rf.joblib"
    print(f"Saving model to {model_path}")
    joblib.dump(pipeline, model_path)

    # Create model card
    model_version = datetime.now().strftime("%Y%m%d_rf_v1")
    model_card = {
        "model_name": "sklearn-random-forest",
        "model_version": model_version,
        "artifact_path": "model/energy_rf.joblib",
        "target_variable": "SourceEUIWN(kBtu/sf)",
        "predicted_field": "predicted_source_eui_wn_kbtu_sf",
        "algorithm": "RandomForestRegressor",
        "preprocessing": {
            "numeric_strategy": "median_imputation",
            "categorical_strategy": "most_frequent_imputation + one_hot_encoding",
        },
        "feature_contract": {
            "numeric": [
                "ENERGYSTARScore",
                "NumberofBuildings",
                "NumberofFloors",
                "PropertyGFATotal",
                "YearBuilt",
            ],
            "categorical": [
                "BuildingType",
                "PrimaryPropertyType",
                "LargestPropertyUseType",
                "Neighborhood",
            ],
        },
        "validation_rules": {
            "ENERGYSTARScore": {"min": 0, "max": 100},
            "NumberofBuildings": {"min": 1},
            "NumberofFloors": {"min": 1},
            "PropertyGFATotal": {"min": 1},
            "YearBuilt": {"min": 1800, "max": datetime.now().year},
        },
        "performance_metrics": metrics,
        "training_date": datetime.now().isoformat(),
        "sklearn_version": "1.4.2",
    }

    # Save model card
    card_path = output_dir / "model_card.json"
    print(f"Saving model card to {card_path}")
    with open(card_path, "w") as f:
        json.dump(model_card, f, indent=2)

    print(f"Training complete! Model version: {model_version}")


def main() -> None:
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train energy use prediction model")
    parser.add_argument("--csv", type=Path, required=True, help="Path to the CSV data file")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("model"),
        help="Output directory for model artifacts",
    )

    args = parser.parse_args()

    # Load and prepare data
    X, y = load_and_prepare_data(args.csv)  # noqa: N806

    # Train model
    pipeline, metrics = train_model(X, y)

    # Save artifacts
    save_artifacts(pipeline, metrics, args.out)


if __name__ == "__main__":
    main()
