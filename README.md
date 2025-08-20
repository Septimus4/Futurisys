# Energy Use Prediction API

A production-ready POC for predicting building energy intensity using a scikit-learn RandomForest model, exposed via FastAPI with PostgreSQL persistence.

## Overview

This API predicts building energy use intensity (SourceEUIWN in kBtu/sf) based on building characteristics using a trained RandomForest model. Every request and result is persisted to PostgreSQL for audit and analytics.

### Key Features

- **FastAPI** REST API with automatic OpenAPI documentation
- **scikit-learn** RandomForest regression model with preprocessing pipeline
- **PostgreSQL** persistence for all requests, results, and errors
- **Pydantic** validation with strict input constraints
- **Structured logging** with JSON output and request tracing
- **Docker** containerization with docker-compose setup
- **CI/CD** with GitHub Actions (lint, test, build)
- **Optional API key** authentication

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to the repository
git clone <repository-url>
cd energy-prediction-api

# Configure environment (REQUIRED)
cp .env.example .env
# Edit .env with your database password and other settings

# Start the stack (API + PostgreSQL)
docker-compose up --build

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure environment for local development
cp .env.example .env
# Edit .env with your local PostgreSQL connection details

# Create database tables
python migrations/create_db.py

# Start the API
uvicorn src.app:app --reload

# API available at http://localhost:8000
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "model": "sklearn-random-forest",
  "artifact": "model/energy_rf.joblib",
  "version": "20250819_rf_v1"
}
```

### Single Prediction

```bash
curl -X POST http://localhost:8000/predict-energy-eui \
  -H "Content-Type: application/json" \
  -d '{
    "ENERGYSTARScore": 75,
    "NumberofBuildings": 1,
    "NumberofFloors": 12,
    "PropertyGFATotal": 350000,
    "YearBuilt": 1998,
    "BuildingType": "NonResidential",
    "PrimaryPropertyType": "Office",
    "LargestPropertyUseType": "Office",
    "Neighborhood": "DOWNTOWN"
  }'
```

Response:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "predicted_source_eui_wn_kbtu_sf": 68.42,
  "model_name": "sklearn-random-forest",
  "model_version": "20250819_rf_v1",
  "inference_ms": 5
}
```

### Batch Prediction

```bash
curl -X POST http://localhost:8000/predict-energy-eui/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "ENERGYSTARScore": 75,
        "NumberofBuildings": 1,
        "NumberofFloors": 12,
        "PropertyGFATotal": 350000,
        "YearBuilt": 1998,
        "BuildingType": "NonResidential",
        "PrimaryPropertyType": "Office",
        "LargestPropertyUseType": "Office",
        "Neighborhood": "DOWNTOWN"
      },
      {
        "ENERGYSTARScore": 85,
        "NumberofBuildings": 1,
        "NumberofFloors": 8,
        "PropertyGFATotal": 200000,
        "YearBuilt": 2010,
        "BuildingType": "NonResidential",
        "PrimaryPropertyType": "Office",
        "LargestPropertyUseType": "Office",
        "Neighborhood": "BALLARD"
      }
    ]
  }'
```

### Request Lookup

```bash
curl http://localhost:8000/requests/{request_id}
```

## API Documentation

### OpenAPI Specification

The complete API specification is available in multiple formats:

- **Interactive Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **Alternative Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Repository File**: [`openapi.json`](./openapi.json) (version-controlled specification)

### Client Generation

You can generate API clients in various languages using the OpenAPI specification:

```bash
# Using OpenAPI Generator CLI
openapi-generator-cli generate -i openapi.json -g python -o ./client-python
openapi-generator-cli generate -i openapi.json -g typescript-fetch -o ./client-ts
openapi-generator-cli generate -i openapi.json -g java -o ./client-java
```

### Updating OpenAPI Spec

To update the repository's OpenAPI specification file:

```bash
# Automatic update (requires running API)
python scripts/update_openapi.py

# Manual download
curl http://localhost:8000/openapi.json -o openapi.json
```

## Input Validation

### Required Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `NumberofBuildings` | int | ≥ 1 | Number of buildings |
| `NumberofFloors` | int | ≥ 1 | Number of floors |
| `PropertyGFATotal` | float | > 0 | Total gross floor area (sq ft) |
| `YearBuilt` | int | 1800-2025 | Year building was built |
| `BuildingType` | string | 1-100 chars | Building type |
| `PrimaryPropertyType` | string | 1-100 chars | Primary property type |
| `LargestPropertyUseType` | string | 1-100 chars | Largest property use type |
| `Neighborhood` | string | 1-100 chars | Neighborhood name |

### Optional Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `ENERGYSTARScore` | float | 0-100 | ENERGY STAR score |

### Limits

- Single request body: ≤ 16 KB
- Batch request body: ≤ 1 MB
- Batch size: ≤ 512 items
- Inference timeout: 5 seconds

## Authentication

API key authentication is optional and enabled by setting the `API_KEY` environment variable.

```bash
# With API key enabled
curl -X POST http://localhost:8000/predict-energy-eui \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '...'
```

## Model Information

### Algorithm
- **RandomForestRegressor** with 100 estimators
- **Preprocessing Pipeline**:
  - Numeric features: Median imputation
  - Categorical features: Most frequent imputation + One-hot encoding

### Features Used
- **Numeric**: ENERGYSTARScore, NumberofBuildings, NumberofFloors, PropertyGFATotal, YearBuilt
- **Categorical**: BuildingType, PrimaryPropertyType, LargestPropertyUseType, Neighborhood

### Performance
- **R²**: ~0.21 (on test set)
- **MAE**: ~49 kBtu/sf
- **RMSE**: ~160 kBtu/sf

## Training Data

The model is trained on the Seattle 2016 Building Energy Benchmarking dataset, predicting `SourceEUIWN(kBtu/sf)` (weather-normalized source energy use intensity).

### Retraining the Model

```bash
# Download fresh data and retrain
python src/train_stub.py \
  --csv ./2016_Building_Energy_Benchmarking.csv \
  --out ./model

# The API will automatically pick up the new model on restart
```

## Environment Configuration

**IMPORTANT: Configure environment variables before running!**

This project requires environment configuration for database connections, API keys, and other settings.

### Quick Setup

1. **Automated setup (recommended):**
   ```bash
   ./scripts/setup_env.sh
   ```

2. **Manual setup:**
   ```bash
   cp .env.example .env
   nano .env  # Update DATABASE_URL, passwords, and API keys
   ```

3. **Validate configuration:**
   ```bash
   python scripts/validate_env.py
   ```

4. **For detailed configuration guide:**
   See [ENVIRONMENT.md](./ENVIRONMENT.md) for complete setup instructions.

### Key Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes      | PostgreSQL connection URL |
| `POSTGRES_PASSWORD` | Yes      | Database password (for docker-compose) |
| `API_KEY` | No       | Optional API key for authentication |
| `LOG_LEVEL` | No       | Logging level (default: INFO) |

**Note:** All hardcoded credentials have been removed. You MUST configure these variables.

## Database Schema

### Tables

1. **inference_request**: Stores all incoming requests
2. **inference_result**: Stores successful predictions
3. **inference_error**: Stores error details

### Example Queries

```sql
-- Recent predictions
SELECT r.id, r.received_at, res.predicted_source_eui_wn_kbtu_sf 
FROM inference_request r 
JOIN inference_result res ON r.id = res.request_id 
ORDER BY r.received_at DESC LIMIT 10;

-- Error analysis
SELECT error_type, COUNT(*) 
FROM inference_error 
GROUP BY error_type;

-- Daily request volume
SELECT DATE(received_at) as date, COUNT(*) as requests
FROM inference_request 
GROUP BY DATE(received_at) 
ORDER BY date DESC;
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Train a test model first (pre-trained model included)
# python src/train_stub.py --csv ./2016_Building_Energy_Benchmarking.csv --out ./model

# Quick test script (matches CI)
./scripts/test.sh --coverage  # Full test suite with coverage
./scripts/test.sh --fast      # Skip integration tests 
./scripts/test.sh --lint      # Linting and type checking only

# Manual test commands
python -m pytest tests/ --cov=src --cov-report=html -v  # All tests with coverage
python -m pytest tests/test_integration.py -v           # Integration tests only
```

### Integration Tests & Demo

The project includes comprehensive integration tests that demonstrate real-world usage scenarios and serve as regression tests:

```bash
# Run integration tests (realistic building scenarios)
pytest tests/test_integration.py -v

# Interactive demo (requires running API)
python demo.py
```

**Integration Test Scenarios:**
- Small office building (25k sq ft, downtown)
- Large retail complex (150k sq ft, suburban)
- High-efficiency green building (ENERGY STAR 95)
- Historic building (1920s construction)
- Very large building (500k sq ft)
- Mixed-use property
- Building portfolio analysis (batch processing)
- Performance regression checks
- API response format stability

**Demo Features:**
- Live API health checking
- Real-world building prediction examples
- Portfolio analysis demonstration
- Edge case handling
- Performance timing
- Integration guidance

The integration tests ensure the API works correctly for diverse building types and serve as executable documentation for common use cases.

## CI/CD Pipeline

### GitHub Actions

The project includes a comprehensive CI/CD pipeline with multiple jobs:

**Lint Job:**
- Code formatting with `ruff format`
- Linting and type checking with `ruff check`

**Test Job:**
- Unit and validation tests with 75%+ coverage requirement
- Uses pre-trained model (no training in CI)
- PostgreSQL service for database tests
- Coverage reporting with HTML and XML output
- Codecov integration for coverage tracking

**Integration Test Job:**
- Real-world scenario testing
- Demo script validation
- Separate job for faster parallel execution

**Build Job:**
- Docker image build and validation
- Container startup testing
- Health endpoint verification

### Coverage Reporting

```bash
# Coverage configuration in pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "src/train_stub.py"]

[tool.coverage.report]
fail_under = 75
show_missing = true
```

**Coverage Targets:**
- Overall: 75% minimum (currently 80%+)
- HTML reports generated for detailed analysis
- Missing lines clearly identified
- Excludes training script and test files

### Local CI Simulation

```bash
# Run the same checks as CI locally
./scripts/test.sh --coverage

# Quick checks before pushing
./scripts/test.sh --lint
```

### Code Quality

```bash
# Linting and formatting (all-in-one with ruff)
ruff check src tests
ruff format src tests
```

### Project Structure

```
.
├── src/
│   ├── app.py           # FastAPI application
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── service.py       # Business logic and persistence
│   ├── runtime.py       # Model loading and prediction
│   ├── deps.py          # Dependency injection
│   ├── settings.py      # Configuration management
│   └── train_stub.py    # Model training script
├── tests/               # Test suite
├── model/               # Model artifacts
├── migrations/          # Database setup
├── scripts/             # Utility scripts
│   └── update_openapi.py # OpenAPI spec updater
├── openapi.json         # API specification (version-controlled)
├── Dockerfile           # Container definition
├── docker-compose.yml   # Local stack
└── .github/workflows/   # CI/CD pipeline
```

## Deployment

### Production Considerations

1. **Database**: Use managed PostgreSQL (AWS RDS, GCP Cloud SQL, etc.)
2. **Security**: Enable API key authentication, use HTTPS
3. **Monitoring**: Add metrics collection (Prometheus/Grafana)
4. **Scaling**: Deploy multiple API instances behind a load balancer
5. **Model Updates**: Implement blue-green deployment for model updates

### Docker Production

```bash
# Build production image
docker build -t energy-prediction-api:prod .

# Run with production config
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e API_KEY="secure-key" \
  -e LOG_LEVEL="WARNING" \
  energy-prediction-api:prod
```

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure `model/energy_rf.joblib` exists
2. **Database connection**: Verify PostgreSQL is running and credentials are correct
3. **Permission errors**: Check file permissions for model artifacts
4. **Memory issues**: Monitor memory usage during batch predictions

### Logs

```bash
# View structured logs in development
docker-compose logs api

# Check health endpoint
curl http://localhost:8000/health

# View database connections
docker-compose exec db psql -U user -d energy_poc -c "SELECT * FROM pg_stat_activity;"
```

### Performance Tuning

- **Batch size**: Adjust `MAX_BATCH_SIZE` based on memory constraints
- **Connection pooling**: Tune PostgreSQL connection pool settings
- **Model caching**: Model is loaded once at startup and cached

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI spec**: http://localhost:8000/openapi.json

## License

This is a POC implementation. Adjust licensing as needed for your use case.
