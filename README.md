# Zero-Shot Text Classification API (POC)

Production-lean proof-of-concept FastAPI service wrapping Hugging Face `facebook/bart-large-mnli` zero-shot classification with full request/response persistence in PostgreSQL, JSON structured logging, simple API key auth, and test/CI setup.

## Features

- Zero-shot classification via HF transformers (model loaded once at startup)
- `/health`, `/classify`, `/requests/{id}` endpoints
- PostgreSQL persistence of requests, results, and errors
- JSON structured logging with per-request UUID and latency
- Optional API key auth via `X-API-Key`
- Timeout & validation safeguards
- Docker + docker-compose (API + Postgres)
- Tests (pytest + httpx) with coverage, lint (ruff), types (mypy), CI workflow

## Quick Start (Docker)

```bash
docker-compose up --build
```

Then open: http://localhost:8000/docs

Classify example:

```bash
curl -X POST http://localhost:8000/classify \
	-H 'Content-Type: application/json' \
	-d '{"text":"I love writing Python","candidate_labels":["technology","sports"],"multi_label":false}'
```

## Local Dev (Without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/zero_shot
python migrations/create_db.py
uvicorn src.app:app --reload
```

Or install only runtime deps:

```bash
pip install .
```
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | REQUIRED | Postgres URL (sqlalchemy) |
| `API_KEY` | unset | If set, required via `X-API-Key` header |
| `MODEL_NAME` | `facebook/bart-large-mnli` | HF model id |
| `LOG_LEVEL` | `INFO` | Logging level |
| `INFERENCE_TIMEOUT_SECONDS` | `10` | Max seconds per inference |

## Endpoints

### GET /health
Returns status and model.

### POST /classify
Body:
```json
{
	"text": "I love writing Python and deploying models.",
	"candidate_labels": ["technology", "sports", "finance"],
	"multi_label": false,
	"hypothesis_template": "This text is about {}"
}
```
Returns ordered labels & scores.

### GET /requests/{request_id}
Retrieve stored request + result or error.

## Testing

```bash
pytest --cov=src --cov-report=term-missing
```

Mocked pipeline used for most tests; integration test may download model (marked `slow`).

## CI

GitHub Actions workflow runs: lint (ruff), type check (mypy), tests + coverage, Docker build.

## OpenAPI / Swagger
Auto-generated docs: visit `http://localhost:8000/docs`

Static spec file: `docs/openapi.yaml` (manually curated, may slightly differ from live schema). Use:
```bash
curl -s http://localhost:8000/openapi.json | jq '.info'
```

## Architecture

See `docs/architecture.md` for a detailed overview of components, request lifecycle, schema, error handling, and extension paths.

## Data Model
See `src/models.py` and `migrations/create_db.py` for table definitions: `inference_request`, `inference_result`, `inference_error`.

## Observability
- Per-request UUID `request_id`
- JSON logs (stdout)
- Latency captured in ms

## Security (POC)
- Optional API key header. Only masked/hash prefix stored.

## License
POC – unspecified (add a license file if distributing).
