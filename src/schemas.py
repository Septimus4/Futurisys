from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_TEXT = 20_000
MAX_LABELS = 50


def _normalize_label(label: str) -> str:
    return label.strip()


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT)
    candidate_labels: list[str] = Field(..., min_length=2, max_length=MAX_LABELS)
    multi_label: bool = False
    hypothesis_template: str | None = Field(None, max_length=256)

    @field_validator("text")
    @classmethod
    def valid_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty or whitespace")
        return v.strip()

    @field_validator("candidate_labels")
    @classmethod
    def valid_labels(cls, v: list[str]) -> list[str]:
        normed: list[str] = []
        seen_lower: set[str] = set()
        for label in v:
            lbl = _normalize_label(label)
            if not (1 <= len(lbl) <= 64):
                raise ValueError("each label must be 1..64 chars")
            lower = lbl.lower()
            if lower in seen_lower:
                continue
            seen_lower.add(lower)
            normed.append(lbl)
        if len(normed) < 2:
            raise ValueError("need at least two unique labels")
        return normed

    @model_validator(mode="after")
    def set_default_template(self) -> ClassifyRequest:
        if not self.hypothesis_template:
            self.hypothesis_template = "This example is {}."
        return self


class ClassifyResponse(BaseModel):
    request_id: uuid.UUID
    labels: list[str]
    scores: list[float]
    top_label: str
    inference_ms: int


class StoredRequest(BaseModel):
    id: uuid.UUID
    text: str
    candidate_labels: list[str]
    multi_label: bool
    hypothesis_template: str | None


class StoredResult(BaseModel):
    request_id: uuid.UUID
    labels: list[str]
    scores: list[float]
    top_label: str
    inference_ms: int


class StoredError(BaseModel):
    request_id: uuid.UUID
    error_type: str
    message: str


class RequestRecord(BaseModel):
    request: StoredRequest
    result: StoredResult | None = None
    error: StoredError | None = None
