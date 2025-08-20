"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnergyPredictionRequest(BaseModel):
    """Schema for energy prediction request."""

    # Numeric features
    ENERGYSTARScore: float | None = Field(None, ge=0, le=100, description="ENERGY STAR score (0-100)")
    NumberofBuildings: int = Field(..., ge=1, description="Number of buildings (≥1)")
    NumberofFloors: int = Field(..., ge=1, description="Number of floors (≥1)")
    PropertyGFATotal: float = Field(..., gt=0, description="Total gross floor area in square feet (>0)")
    YearBuilt: int = Field(
        ...,
        ge=1800,
        le=datetime.now().year,
        description=f"Year built (1800-{datetime.now().year})",
    )

    # Categorical features
    BuildingType: str = Field(..., min_length=1, max_length=100, description="Building type")
    PrimaryPropertyType: str = Field(..., min_length=1, max_length=100, description="Primary property type")
    LargestPropertyUseType: str = Field(..., min_length=1, max_length=100, description="Largest property use type")
    Neighborhood: str = Field(..., min_length=1, max_length=100, description="Neighborhood")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, protected_namespaces=())

    @field_validator("BuildingType", "PrimaryPropertyType", "LargestPropertyUseType", "Neighborhood")
    @classmethod
    def validate_categorical_fields(cls, v: str) -> str:
        """Validate and normalize categorical fields."""
        if not v or not v.strip():
            raise ValueError("Categorical fields cannot be empty")
        return v.strip()


class EnergyPredictionResponse(BaseModel):
    """Schema for energy prediction response."""

    request_id: uuid.UUID = Field(..., description="Unique identifier for this request")
    predicted_source_eui_wn_kbtu_sf: float = Field(..., description="Predicted source energy use intensity in kBtu/sf")
    model_name: str = Field(..., description="Model name used for prediction")
    model_version: str = Field(..., description="Model version used for prediction")
    inference_ms: int = Field(..., description="Time taken for inference in milliseconds")

    model_config = ConfigDict(protected_namespaces=())


class BatchPredictionRequest(BaseModel):
    """Schema for batch prediction request."""

    items: list[EnergyPredictionRequest] = Field(
        ...,
        min_length=1,
        max_length=512,
        description="List of prediction requests (max 512)",
    )

    model_config = ConfigDict(extra="forbid")


class BatchPredictionResult(BaseModel):
    """Schema for individual batch prediction result."""

    index: int = Field(..., description="Index of the item in the batch")
    predicted_source_eui_wn_kbtu_sf: float = Field(..., description="Predicted source energy use intensity in kBtu/sf")


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction response."""

    request_id: uuid.UUID = Field(..., description="Unique identifier for this batch request")
    results: list[BatchPredictionResult] = Field(..., description="List of prediction results")
    inference_ms: int = Field(..., description="Total time taken for batch inference in milliseconds")


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(default="ok", description="Health status")
    model: str = Field(..., description="Model type identifier")
    artifact: str = Field(..., description="Path to model artifact")
    version: str = Field(..., description="Model version")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    request_id: uuid.UUID | None = Field(None, description="Request ID if available")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class RequestLookupResponse(BaseModel):
    """Schema for request lookup response."""

    request_id: uuid.UUID = Field(..., description="Request identifier")
    received_at: datetime = Field(..., description="When the request was received")
    features: dict[str, Any] = Field(..., description="Original request features")
    result: EnergyPredictionResponse | None = Field(None, description="Prediction result if successful")
    error: ErrorResponse | None = Field(None, description="Error details if failed")
