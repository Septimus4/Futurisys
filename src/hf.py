from __future__ import annotations

from functools import lru_cache
from typing import Protocol, TypedDict

import torch
from transformers import Pipeline, pipeline

from .settings import get_settings


class ZeroShotResultDict(TypedDict):
    labels: list[str]
    scores: list[float]
    sequence: str


class ZeroShotPipeline(Protocol):  # pragma: no cover - structural
    def __call__(
        self,
        sequences: str | list[str],
        *,
        candidate_labels: list[str] | str,
        hypothesis_template: str | None = None,
        multi_label: bool | None = None,
    ) -> ZeroShotResultDict | list[ZeroShotResultDict]: ...


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
    except Exception:
        if model_name != "valhalla/distilbart-mnli-12-1":
            pipe = pipeline(
                "zero-shot-classification",
                model="valhalla/distilbart-mnli-12-1",
                device=-1,
            )
        else:
            raise
    torch.set_grad_enabled(False)
    return pipe
