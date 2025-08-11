from __future__ import annotations

from functools import lru_cache
from transformers import pipeline, Pipeline
from .settings import get_settings
import torch


@lru_cache
def get_pipeline() -> Pipeline:  # pragma: no cover (heavy)
    settings = get_settings()
    model_name = settings.model_name
    try:
        pipe = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=-1,  # CPU
        )
    except Exception:  # noqa: BLE001
        if model_name != "valhalla/distilbart-mnli-12-1":
            pipe = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1", device=-1)
        else:
            raise
    torch.set_grad_enabled(False)
    return pipe
