"""SQLAlchemy database models for energy prediction API."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class InferenceRequest(Base):
    """Model for storing inference requests."""

    __tablename__ = "inference_request"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    features: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Validated and normalized input features"
    )
    api_key_used: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="Masked/hash prefix of API key used"
    )

    # Relationships
    result: Mapped[Optional["InferenceResult"]] = relationship(
        "InferenceResult", back_populates="request", cascade="all, delete-orphan"
    )
    error: Mapped[Optional["InferenceError"]] = relationship(
        "InferenceError", back_populates="request", cascade="all, delete-orphan"
    )


class InferenceResult(Base):
    """Model for storing successful inference results."""

    __tablename__ = "inference_result"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inference_request.id"), primary_key=True
    )
    predicted_source_eui_wn_kbtu_sf: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
        comment="Predicted energy use intensity in kBtu/sf",
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    inference_ms: Mapped[int] = mapped_column(Integer, nullable=False, comment="Inference time in milliseconds")
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    request: Mapped["InferenceRequest"] = relationship("InferenceRequest", back_populates="result")


class InferenceError(Base):
    """Model for storing inference errors."""

    __tablename__ = "inference_error"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inference_request.id"), primary_key=True
    )
    error_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of error (validation, inference, timeout, etc.)",
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="Error message")
    traceback: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Python traceback for debugging")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    request: Mapped["InferenceRequest"] = relationship("InferenceRequest", back_populates="error")
