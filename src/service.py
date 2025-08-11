from __future__ import annotations

import logging
import time
import traceback as tb
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import cast

from sqlalchemy.orm import Session

# Import the hf module (not the function directly) so tests can monkeypatch
# hf.get_pipeline reliably. Importing the symbol directly makes monkeypatching
# harder because the reference is bound at import time.
from . import hf
from .models import InferenceError, InferenceRequest, InferenceResult
from .schemas import ClassifyRequest, ClassifyResponse
from .settings import get_settings


class InferenceProcessError(Exception):  # kept for potential future differentiation
    """Domain-specific inference exception (unused presently)."""
    pass


def classify_and_persist(
    payload: ClassifyRequest, db: Session, api_key_hash: str | None
) -> ClassifyResponse:
    request_id = uuid.uuid4()
    inf_req = InferenceRequest(
        id=request_id,
        text=payload.text,
        candidate_labels=payload.candidate_labels,
        multi_label=payload.multi_label,
        hypothesis_template=payload.hypothesis_template,
        api_key_used=api_key_hash,
    )
    db.add(inf_req)
    db.flush()

    start = time.perf_counter()
    settings = get_settings()
    pipe = hf.get_pipeline()

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(
                pipe,
                payload.text,
                candidate_labels=payload.candidate_labels,
                hypothesis_template=payload.hypothesis_template,
                multi_label=payload.multi_label,
            )
            result = fut.result(timeout=settings.inference_timeout_seconds)
    except FuturesTimeout:  # timeout handling
        trace = tb.format_exc()
        inf_err = InferenceError(
            request_id=request_id,
            error_type="TimeoutError",
            message=(
                f"inference exceeded {settings.inference_timeout_seconds}s"
            ),
            traceback=trace,
        )
        db.add(inf_err)
        db.commit()
        raise
    except Exception as e:
        trace = tb.format_exc()
        inf_err = InferenceError(
            request_id=request_id,
            error_type=e.__class__.__name__,
            message=str(e),
            traceback=trace,
        )
        db.add(inf_err)
        db.commit()
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    # The pipeline returns ZeroShotResultDict (enforced via Protocol/TypedDict)
    result_map = cast("hf.ZeroShotResultDict", result)
    labels = list(result_map["labels"])
    scores = list(result_map["scores"])
    top_label = labels[0] if labels else ""

    inf_res = InferenceResult(
        request_id=request_id,
        labels=labels,
        scores=scores,
        top_label=top_label,
        inference_ms=elapsed_ms,
    )
    db.add(inf_res)
    db.commit()

    logging.getLogger(__name__).debug(
        "classification complete", extra={
            "request_id": str(request_id),
            "labels": labels,
            "elapsed_ms": elapsed_ms,
        }
    )

    return ClassifyResponse(
        request_id=request_id,
        labels=labels,
        scores=scores,
        top_label=top_label,
        inference_ms=elapsed_ms,
    )
