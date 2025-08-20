"""Test configuration and fixtures."""

from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.app import app
from src.deps import get_db
from src.models import Base
from src.runtime import model_runtime

# Test database URL (uses in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def setup_test_db() -> None:
    """Create all database tables for testing."""
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db(setup_test_db: None) -> None:
    """Set up test database - this fixture runs automatically."""
    pass


@pytest.fixture
def db_session(setup_test_db: None) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: db_session

    # Mock the database engine creation to skip database connection during app startup
    def mock_create_tables() -> None:
        pass

    monkeypatch.setattr("src.deps.create_tables", mock_create_tables)

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def async_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    app.dependency_overrides[get_db] = lambda: db_session

    # Mock the database engine creation
    def mock_create_tables() -> None:
        pass

    monkeypatch.setattr("src.deps.create_tables", mock_create_tables)

    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def load_model() -> None:
    """Load the model once for all tests."""
    try:
        model_runtime.load_artifacts()
    except FileNotFoundError:
        pytest.skip("Model artifacts not found - run training first")


@pytest.fixture
def sample_prediction_request() -> dict[str, Any]:
    """Sample valid prediction request."""
    return {
        "ENERGYSTARScore": 75,
        "NumberofBuildings": 1,
        "NumberofFloors": 12,
        "PropertyGFATotal": 350000,
        "YearBuilt": 1998,
        "BuildingType": "NonResidential",
        "PrimaryPropertyType": "Office",
        "LargestPropertyUseType": "Office",
        "Neighborhood": "DOWNTOWN",
    }


@pytest.fixture
def sample_batch_request(
    sample_prediction_request: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Sample valid batch prediction request."""
    return {
        "items": [
            sample_prediction_request,
            {
                **sample_prediction_request,
                "PropertyGFATotal": 200000,
                "NumberofFloors": 8,
            },
        ]
    }
