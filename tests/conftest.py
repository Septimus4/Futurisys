from __future__ import annotations

import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set env before importing app/settings
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("MODEL_NAME", "facebook/bart-large-mnli")

from src.app import app  # type: ignore  # noqa: E402
from src.models import Base  # type: ignore  # noqa: E402
from src.deps import get_db  # type: ignore  # noqa: E402
from src import hf as hf_module  # type: ignore  # noqa: E402

TEST_DB_URL = "sqlite+pysqlite:///./test_unit.db"  # file-based to keep schema across connections

@pytest.fixture(autouse=True)
def mock_pipeline(monkeypatch):
    class MockPipe:
        def __call__(self, text, candidate_labels, hypothesis_template, multi_label):  # noqa: D401
            labels = list(candidate_labels)
            base = 1.0 / max(len(labels), 1)
            scores = [base for _ in labels]
            return {"labels": labels, "scores": scores}

    monkeypatch.setattr(hf_module, "get_pipeline", lambda: MockPipe())
    yield

@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
