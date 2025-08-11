from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InferenceRequest(Base):
    __tablename__ = "inference_request"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    received_at: Mapped[datetime] = mapped_column(default=utcnow)
    text: Mapped[str]
    candidate_labels: Mapped[list[str]] = mapped_column(JSON)
    multi_label: Mapped[bool]
    hypothesis_template: Mapped[str | None]
    api_key_used: Mapped[str | None]


class InferenceResult(Base):
    __tablename__ = "inference_result"

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inference_request.id", ondelete="CASCADE"), primary_key=True)
    labels: Mapped[list[str]] = mapped_column(JSON)
    scores: Mapped[list[float]] = mapped_column(JSON)
    top_label: Mapped[str]
    inference_ms: Mapped[int]
    completed_at: Mapped[datetime] = mapped_column(default=utcnow)


class InferenceError(Base):
    __tablename__ = "inference_error"

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inference_request.id", ondelete="CASCADE"), primary_key=True)
    error_type: Mapped[str]
    message: Mapped[str]
    traceback: Mapped[str]
    occurred_at: Mapped[datetime] = mapped_column(default=utcnow)
