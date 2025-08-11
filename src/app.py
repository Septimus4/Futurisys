from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .deps import get_db, get_engine, verify_api_key
from .hf import get_pipeline
from .models import Base, InferenceError, InferenceRequest, InferenceResult
from .schemas import (
    ClassifyRequest,
    ClassifyResponse,
    RequestRecord,
    StoredError,
    StoredRequest,
    StoredResult,
)
from .service import classify_and_persist
from .settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover - side effects
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(message)s',  # emit pure JSON strings already encoded below
    )
    logger = logging.getLogger(__name__)
    get_pipeline()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info(json.dumps({"event": "startup"}))
    try:
        yield
    finally:
        logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title="Zero-Shot Classification API",
    version=get_settings().app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_timing_and_request_id(
    request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]
) -> JSONResponse:  # middleware signature
    rid = uuid.uuid4()
    request.state.request_id = rid
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        body = {"request_id": str(rid), "error": "internal server error"}
        response = JSONResponse(status_code=500, content=body)
        logging.getLogger("request").error(json.dumps({
            "request_id": str(rid),
            "path": request.url.path,
            "method": request.method,
            "status": 500,
            "duration_ms": elapsed,
            "error_type": e.__class__.__name__,
            "message": str(e),
        }))
        raise
    elapsed = int((time.perf_counter() - start) * 1000)
    logging.getLogger("request").info(json.dumps({
        "request_id": str(rid),
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "duration_ms": elapsed,
    }))
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "model": settings.model_name, "version": settings.app_version}


@app.post("/classify", response_model=ClassifyResponse)
async def classify(
    payload: ClassifyRequest,
    db: Session = Depends(get_db),
    api_key_hash: str | None = Depends(verify_api_key),
) -> ClassifyResponse:
    try:
        resp = classify_and_persist(payload, db, api_key_hash)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        # surface error for POC test visibility
        raise HTTPException(status_code=500, detail=f"inference failed: {e}") from e


@app.get("/requests/{request_id}", response_model=RequestRecord)
async def get_request(request_id: uuid.UUID, db: Session = Depends(get_db)) -> RequestRecord:
    req = db.get(InferenceRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="not found")
    res = db.get(InferenceResult, request_id)
    err = db.get(InferenceError, request_id)
    return RequestRecord(
        request=StoredRequest(
            id=req.id,
            text=req.text,
            candidate_labels=req.candidate_labels,
            multi_label=req.multi_label,
            hypothesis_template=req.hypothesis_template,
        ),
        result=(
            StoredResult(
                request_id=res.request_id,
                labels=res.labels,
                scores=res.scores,
                top_label=res.top_label,
                inference_ms=res.inference_ms,
            )
            if res else None
        ),
        error=(
            StoredError(
                request_id=err.request_id,
                error_type=err.error_type,
                message=err.message,
            )
            if err else None
        ),
    )
