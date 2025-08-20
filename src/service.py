"""Service layer for handling business logic and persistence."""

import contextlib
import traceback
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import InferenceError, InferenceRequest, InferenceResult
from .runtime import model_runtime
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    BatchPredictionResult,
    EnergyPredictionRequest,
    EnergyPredictionResponse,
)


class PredictionService:
    """Service for handling energy predictions with persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize the service with a database session."""
        self.db = db

    def _create_request_record(self, features: dict[str, Any], api_key_masked: str | None = None) -> InferenceRequest:
        """Create and persist an inference request record."""
        request = InferenceRequest(id=uuid.uuid4(), features=features, api_key_used=api_key_masked)
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def _save_result(self, request_id: uuid.UUID, prediction: float, inference_ms: int) -> None:
        """Save a successful prediction result."""
        result = InferenceResult(
            request_id=request_id,
            predicted_source_eui_wn_kbtu_sf=prediction,
            model_name=model_runtime.get_model_name(),
            model_version=model_runtime.get_model_version(),
            inference_ms=inference_ms,
        )
        self.db.add(result)
        self.db.commit()

    def _save_error(
        self,
        request_id: uuid.UUID,
        error_type: str,
        message: str,
        tb: str | None = None,
    ) -> None:
        """Save an error record."""
        error = InferenceError(request_id=request_id, error_type=error_type, message=message, traceback=tb)
        self.db.add(error)
        self.db.commit()

    def predict_single(
        self, request: EnergyPredictionRequest, api_key_masked: str | None = None
    ) -> EnergyPredictionResponse:
        """
        Handle a single prediction request with full persistence.

        Args:
            request: Validated prediction request
            api_key_masked: Masked API key for audit trail

        Returns:
            Prediction response

        Raises:
            Exception: Various exceptions for different failure modes
        """
        # Convert request to dict for persistence and prediction
        features = request.model_dump()

        # Create request record
        req_record = self._create_request_record(features, api_key_masked)

        try:
            # Make prediction
            prediction, inference_ms = model_runtime.predict_one(features)

            # Save result
            self._save_result(req_record.id, prediction, inference_ms)

            return EnergyPredictionResponse(
                request_id=req_record.id,
                predicted_source_eui_wn_kbtu_sf=prediction,
                model_name=model_runtime.get_model_name(),
                model_version=model_runtime.get_model_version(),
                inference_ms=inference_ms,
            )

        except Exception as e:
            # Save error
            error_type = type(e).__name__
            message = str(e)
            tb = traceback.format_exc()

            with contextlib.suppress(SQLAlchemyError):
                self._save_error(req_record.id, error_type, message, tb)

            # Re-raise the original exception
            raise

    def predict_batch(
        self, request: BatchPredictionRequest, api_key_masked: str | None = None
    ) -> BatchPredictionResponse:
        """
        Handle a batch prediction request.

        Args:
            request: Validated batch prediction request
            api_key_masked: Masked API key for audit trail

        Returns:
            Batch prediction response

        Raises:
            Exception: Various exceptions for different failure modes
        """
        # Create a single request record for the batch
        batch_features = {
            "batch_size": len(request.items),
            "batch_request": True,
            "items": [item.model_dump() for item in request.items],
        }

        req_record = self._create_request_record(batch_features, api_key_masked)

        try:
            # Convert items to feature dicts
            features_list = [item.model_dump() for item in request.items]

            # Make batch prediction
            predictions, total_inference_ms = model_runtime.predict_batch(features_list)

            # Create results
            results = [
                BatchPredictionResult(index=i, predicted_source_eui_wn_kbtu_sf=pred)
                for i, pred in enumerate(predictions)
            ]

            # Save batch result (store as JSON in the result table)
            {
                "batch_results": [r.model_dump() for r in results],
                "total_inference_ms": total_inference_ms,
            }

            # Use the same result table but store batch data
            result = InferenceResult(
                request_id=req_record.id,
                predicted_source_eui_wn_kbtu_sf=len(predictions),  # Store count as a marker
                model_name=model_runtime.get_model_name(),
                model_version=model_runtime.get_model_version(),
                inference_ms=total_inference_ms,
            )
            self.db.add(result)
            self.db.commit()

            return BatchPredictionResponse(
                request_id=req_record.id,
                results=results,
                inference_ms=total_inference_ms,
            )

        except Exception as e:
            # Save error
            error_type = type(e).__name__
            message = str(e)
            tb = traceback.format_exc()

            with contextlib.suppress(SQLAlchemyError):
                self._save_error(req_record.id, error_type, message, tb)

            raise

    def get_request_by_id(self, request_id: uuid.UUID) -> InferenceRequest | None:
        """
        Retrieve a request by ID with its result or error.

        Args:
            request_id: UUID of the request

        Returns:
            InferenceRequest with loaded relationships, or None if not found
        """
        return self.db.query(InferenceRequest).filter(InferenceRequest.id == request_id).first()
