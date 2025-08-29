"""FastAPI application for energy use prediction."""

import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import deps
from .deps import ApiKeyMasked, DatabaseSession
from .runtime import model_runtime
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    EnergyPredictionRequest,
    EnergyPredictionResponse,
    ErrorResponse,
    HealthResponse,
    RequestLookupResponse,
)
from .service import PredictionService
from .settings import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Energy Prediction API", version=settings.model_version)

    try:
        # Create database tables (via module reference so tests can monkeypatch)
        deps.create_tables()
        logger.info("Database tables created/verified")

        # Load model artifacts
        model_runtime.load_artifacts()
        logger.info("Model artifacts loaded successfully")

    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Energy Prediction API")


# Create FastAPI app
app = FastAPI(
    title="Energy Use Prediction API",
    description="Predict building energy intensity using scikit-learn RandomForest",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Middleware for request/response logging and timing."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    # Log incoming request
    logger.info(
        "Incoming request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
        client_ip=request.client.host if request.client else None,
    )

    try:
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)

        logger.error(
            "Request failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration_ms=duration_ms,
        )

        # Return error response
        error_response = ErrorResponse(
            error="InternalServerError",
            message="An internal error occurred",
            request_id=request_id,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode="json"),
            headers={"X-Request-ID": request_id},
        )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with model metadata."""
    if not model_runtime.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )

    return HealthResponse(
        status="ok",
        model=model_runtime.get_model_name(),
        artifact=model_runtime.get_artifact_path(),
        version=model_runtime.get_model_version(),
    )


@app.post("/predict-energy-eui", response_model=EnergyPredictionResponse)
async def predict_energy_eui(
    request: EnergyPredictionRequest, db: DatabaseSession, api_key_masked: ApiKeyMasked
) -> EnergyPredictionResponse:
    """Predict energy use intensity for a single building."""
    if not model_runtime.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )

    try:
        service = PredictionService(db)
        return service.predict_single(request, api_key_masked)

    except ValueError as e:
        logger.warning("Validation error in prediction", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except TimeoutError as e:
        logger.error("Prediction timeout")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Prediction timeout") from e
    except Exception as e:
        logger.error("Unexpected error in prediction", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@app.post("/predict-energy-eui/batch", response_model=BatchPredictionResponse)
async def predict_energy_eui_batch(
    request: BatchPredictionRequest, db: DatabaseSession, api_key_masked: ApiKeyMasked
) -> BatchPredictionResponse:
    """Predict energy use intensity for multiple buildings."""
    if not model_runtime.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded",
        )

    # Validate batch size
    if len(request.items) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size ({len(request.items)}) exceeds maximum ({settings.max_batch_size})",
        )

    try:
        service = PredictionService(db)
        return service.predict_batch(request, api_key_masked)

    except ValueError as e:
        logger.warning("Validation error in batch prediction", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except TimeoutError as e:
        logger.error("Batch prediction timeout")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Batch prediction request timed out",
        ) from e
    except Exception as e:
        logger.error("Batch prediction error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch prediction failed",
        ) from e


@app.get("/requests/{request_id}", response_model=RequestLookupResponse)
async def get_request(
    request_id: uuid.UUID, db: DatabaseSession, api_key_masked: ApiKeyMasked
) -> RequestLookupResponse:
    """Look up a previous request by ID."""
    service = PredictionService(db)
    req_record = service.get_request_by_id(request_id)

    if not req_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Build response
    result = None
    error = None

    if req_record.result:
        result = EnergyPredictionResponse(
            request_id=req_record.id,
            predicted_source_eui_wn_kbtu_sf=float(req_record.result.predicted_source_eui_wn_kbtu_sf),
            model_name=req_record.result.model_name,
            model_version=req_record.result.model_version,
            inference_ms=req_record.result.inference_ms,
        )

    if req_record.error:
        error = ErrorResponse(
            error=req_record.error.error_type,
            message=req_record.error.message,
            request_id=req_record.id,
        )

    return RequestLookupResponse(
        request_id=req_record.id,
        received_at=req_record.received_at,
        features=req_record.features,
        result=result,
        error=error,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )
