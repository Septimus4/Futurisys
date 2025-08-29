"""Dependency injection for database and authentication."""

import hashlib
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .db_utils import normalize_db_url
from .models import Base
from .settings import settings

db_url = normalize_db_url(settings.database_url)

engine_kwargs: dict[str, object] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": settings.debug,
}

# If using SQLite, configure thread safety for Uvicorn workers
if db_url.startswith("sqlite://"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, **engine_kwargs)
else:
    engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def mask_api_key(api_key: str) -> str:
    """
    Create a masked version of the API key for storage.
    Returns first 8 characters of SHA-256 hash.
    """
    if not api_key:
        return ""

    hash_obj = hashlib.sha256(api_key.encode())
    return hash_obj.hexdigest()[:8]


async def verify_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str | None:
    """
    Verify API key if authentication is enabled.

    Returns:
        Masked API key for logging, or None if auth is disabled
    """
    # If API key is not configured, skip authentication
    if not settings.is_api_key_enabled():
        return None

    # If API key is configured, it's required
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
        )

    # Verify the provided key
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return mask_api_key(x_api_key)


# Type aliases for dependency injection
DatabaseSession = Annotated[Session, Depends(get_db)]
ApiKeyMasked = Annotated[str | None, Depends(verify_api_key)]
