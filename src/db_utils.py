"""Database utility helpers.

This module intentionally has no side effects and no imports from app internals
to avoid circular imports or runtime connections during import time.
"""


def normalize_db_url(url: str) -> str:
    """Normalize DB URL to ensure psycopg3 driver is used and handle postgres://.

    - Convert legacy postgres:// to postgresql://
    - Force driver to psycopg3 (postgresql+psycopg://) when not specified
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url
