from __future__ import annotations

import hashlib
from collections.abc import Generator
from typing import ClassVar

from fastapi import Header, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .settings import get_settings


class Database:
    """Lazy-initialised singleton for Engine + Session factory.

    Avoids module-level mutable globals (and PLW0603 suppression) while
    keeping a simple import-time API surface.
    """

    _instance: ClassVar[Database | None] = None
    _engine: Engine | None
    _SessionLocal: sessionmaker[Session] | None

    def __new__(cls) -> Database:  # pragma: no cover - trivial
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine = None
            cls._instance._SessionLocal = None
        return cls._instance

    # Keep methods tiny (not worth splitting).
    def get_engine(self) -> Engine:  # pragma: no cover - simple
        if self._engine is None:
            settings = get_settings()
            self._engine = create_engine(settings.database_url, pool_pre_ping=True)
        if self._SessionLocal is None:
            self._SessionLocal = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._engine

    def get_session(self) -> Session:
        if self._SessionLocal is None:
            self.get_engine()
        assert self._SessionLocal is not None  # for type-checker
        return self._SessionLocal()


def get_engine() -> Engine:  # facade for existing imports
    return Database().get_engine()


def get_db() -> Generator[Session, None, None]:
    db = Database().get_session()
    try:
        yield db
    finally:  # pragma: no cover - trivial
        db.close()


def verify_api_key(x_api_key: str | None = Header(None)) -> str | None:
    settings = get_settings()
    if settings.api_key is None:
        return None
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")
    # store only hash prefix
    h = hashlib.sha256(x_api_key.encode()).hexdigest()[:12]
    return h
