from __future__ import annotations

import hashlib
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .settings import get_settings
from fastapi import HTTPException, status, Header

_engine = None
_SessionLocal: sessionmaker | None = None


def get_engine():  # pragma: no cover - simple
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)
    return _engine


def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
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
