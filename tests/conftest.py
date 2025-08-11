from __future__ import annotations

import os
import pathlib
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set env before importing app/settings
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("MODEL_NAME", "facebook/bart-large-mnli")

"""Test fixtures.

Imports of application modules occur after environment variables are set; suppress E402.
"""

from src import hf as hf_module  # type: ignore  # noqa: E402
from src.app import app  # type: ignore  # noqa: E402
from src.deps import get_db  # type: ignore  # noqa: E402
from src.models import Base  # type: ignore  # noqa: E402

TEST_DB_URL = "sqlite+pysqlite:///./test_unit.db"  # file-based to keep schema across connections


@pytest.fixture(autouse=True)
def mock_pipeline(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    class MockPipe:
        def __call__(
            self,
            text: str,
            candidate_labels: list[str],
            hypothesis_template: str | None,
            multi_label: bool,
    ) -> dict[str, list[str] | list[float]]:
            labels = list(candidate_labels)
            base = 1.0 / max(len(labels), 1)
            scores = [base for _ in labels]
            return {"labels": labels, "scores": scores}

    monkeypatch.setattr(hf_module, "get_pipeline", lambda: MockPipe())
    yield

@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

    def override_get_db() -> Generator[Session, None, None]:
        db: Session = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
