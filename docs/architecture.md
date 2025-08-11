# Architecture & Internal Documentation

## 1. High-Level Overview

The service exposes a simple HTTP API (FastAPI) that performs zero-shot text classification using a Hugging Face transformers pipeline (BART MNLI) and persists every request, result, and error into a PostgreSQL database. It favors clarity and traceability over advanced optimization.

```
Client ──HTTP──> FastAPI (/classify)
                     │
                     ▼
               Service Layer (classify_and_persist)
                     │
                     ▼
        HF Zero-Shot Pipeline (singleton, CPU)
                     │
                     ▼
              PostgreSQL Persistence
```

## 2. Component Responsibilities

| Component | File(s) | Responsibility |
|-----------|---------|----------------|
| Settings | `src/settings.py` | Load env/config via Pydantic BaseSettings (cached). |
| App (FastAPI) | `src/app.py` | Defines routes, middleware, lifespan (startup), wiring dependencies. |
| Dependencies | `src/deps.py` | Database session factory, API key verification. |
| HF Pipeline | `src/hf.py` | Lazy singleton creation + fallback model. |
| Schemas | `src/schemas.py` | Pydantic models for request/response & stored records. Validation + normalization. |
| ORM Models | `src/models.py` | SQLAlchemy 2.x Declarative models for persistence tables. |
| Service Layer | `src/service.py` | Orchestrates persistence & inference, timeout, error recording. |
| Migrations / Init | `migrations/create_db.py` | Simple metadata create (no Alembic for POC). |
| Tests | `tests/` | Mocked pipeline unit tests + persistence assertions. |

## 3. Request Lifecycle (Classification)

1. HTTP POST `/classify` arrives.
2. Middleware injects `request_id` and measures latency.
3. FastAPI dependency injection provides DB session & optional API key hash.
4. Pydantic model validates and normalizes input: text stripped; labels deduplicated (case-insensitive) & length checked.
5. Service layer persists an `InferenceRequest` row immediately (id + raw inputs).
6. Service layer executes HF pipeline call in a `ThreadPoolExecutor` with timeout (default 10s).
   - On success: produce labels & scores → persist `InferenceResult`.
   - On exception/timeout: persist `InferenceError` (traceback captured) and propagate to route handler (500).
7. Response serialized to JSON including `request_id` and timing logged as JSON line.

## 4. Error Handling & Observability

| Scenario | Persisted? | Response | Notes |
|----------|------------|----------|-------|
| Validation error | No (FastAPI handles) | 422 | Pre-DB; could be extended to persist if desired. |
| Auth failure | No | 401 | API key mismatch. |
| Model timeout | Yes (`InferenceError`) | 500 | `TimeoutError` recorded. |
| HF pipeline exception | Yes | 500 | Traceback stored (internal visibility). |

Structured logging (currently `print` JSON) includes: `level`, `request_id`, `path`, `method`, `status`, `duration_ms` and error metadata when applicable. Could be swapped to `structlog` with minimal change.

## 5. FastAPI App Details

### Lifespan
Executed once: loads pipeline (warm start) and ensures tables exist (`Base.metadata.create_all`). In production you would normally rely on migrations, not auto-create.

### Middleware
`add_timing_and_request_id`:
* Assigns a UUID4 per request.
* Measures elapsed wall-clock time.
* Emits JSON log after completion or on exception.

### Endpoints
* `GET /health` – Static health & model metadata.
* `POST /classify` – Main inference endpoint.
* `GET /requests/{request_id}` – Lookup persisted record (request + result or error).

### Dependencies
* `get_db()` – Yields SQLAlchemy Session (no autocommit; explicit commit in service layer).
* `verify_api_key()` – Conditional API key check (only if env var set) returning a SHA-256 hash prefix stored in DB.

## 6. Database Schema

Using three tables for append-only log style auditing. All times in UTC.

### 6.1 Tables

#### inference_request
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | Generated app-side. |
| received_at | timestamptz | Default now. |
| text | text | Raw input text (consider length constraints). |
| candidate_labels | json | Array of original candidate labels (deduped). |
| multi_label | boolean | Multi vs single label ranking. |
| hypothesis_template | text nullable | Template used for NLI hypothesis. |
| api_key_used | text nullable | Hash prefix of API key (privacy). |

#### inference_result
| Column | Type | Notes |
|--------|------|-------|
| request_id | UUID (PK, FK) | Matches `inference_request.id`. |
| labels | json | Ordered labels returned by pipeline. |
| scores | json | Probabilities/scores (float). |
| top_label | text | Convenience field (`labels[0]`). |
| inference_ms | integer | Duration of inference operation. |
| completed_at | timestamptz | Default now. |

#### inference_error
| Column | Type | Notes |
|--------|------|-------|
| request_id | UUID (PK, FK) | Matches `inference_request.id`. |
| error_type | text | Exception class or `TimeoutError`. |
| message | text | Exception message or timeout explanation. |
| traceback | text | Full Python traceback (internal use). |
| occurred_at | timestamptz | Default now. |

### 6.2 Relationships & Integrity
* `inference_result.request_id` and `inference_error.request_id` reference `inference_request.id` with `ON DELETE CASCADE` (cleanup cascade if you purge requests).
* Exactly one of `inference_result` or `inference_error` should exist per `inference_request` after processing (mutually exclusive). The service logic enforces this invariant; the schema is permissive.

### 6.3 Query Patterns
* Typical lookup: join request + result (or error) by request_id.
* Audit / analytics: time window scan on `received_at` (consider adding index if large volume).

### 6.4 Potential Future Indices
| Suggested Index | Rationale |
|-----------------|-----------|
| `idx_inference_request_received_at` | Range queries by time. |
| `idx_inference_result_top_label` | Filtering by predicted class. |
| Partial index on `inference_error(error_type)` | Error analytics. |

## 7. Inference Flow & Timeout Strategy
The HF pipeline call runs in a single-thread executor with a configurable timeout (`INFERENCE_TIMEOUT_SECONDS`). On timeout a `TimeoutError` entry is persisted; the client receives HTTP 500. (Could be changed to 504 in a future enhancement.)

## 8. Validation & Normalization
Implemented in `schemas.ClassifyRequest`:
* Text stripped & non-empty enforced.
* Candidate labels trimmed, deduplicated (case-insensitive), length 1..64.
* At least two unique labels required.
* Hypothesis template default applied if absent.

## 9. Security Considerations (POC Scope)
* Optional API key header; absence disables auth.
* Only a hash prefix of the key stored (not reversible).
* Full request text stored in DB – if PII concerns arise, add redaction or encryption.

## 10. Extensibility Paths
| Extension | Approach |
|-----------|----------|
| Additional models | Add model registry + dynamic selection param. |
| Batch classification | Accept arrays of inputs; loop or batch in pipeline. |
| Async inference queue | Offload to worker (Celery / RQ) and poll results. |
| Structured logging | Replace print with `structlog` + processor chain. |
| Auth expansion | JWT or OAuth2 dependency layer. |
| Migrations | Introduce Alembic for versioned schema changes. |

## 11. Known Trade-offs
* Simplicity favored over strict domain constraints (no unique composite constraints enforcing single result or error).
* Timeout returns 500 for brevity (could refine to 504).
* Auto-creating tables at startup bypasses formal migrations.
* In-memory testing replaced with file-based SQLite due to multi-connection issues with metadata creation + threads.

## 12. Sequence Example

```
POST /classify
 → validate payload
 → INSERT inference_request
 → run HF pipeline (timeout N seconds)
   ↳ success: INSERT inference_result, COMMIT → 200 JSON
   ↳ failure/timeout: INSERT inference_error, COMMIT → 500 JSON
```

## 13. Glossary
| Term | Definition |
|------|------------|
| Zero-shot | Assign labels without model fine-tuning using NLI formulation. |
| Hypothesis Template | Text pattern converting label into NLI hypothesis ("This example is {label}."). |
| Request ID | UUID used for correlation across logs and DB rows. |

---
Questions or contributions: open an issue or submit a PR with proposed schema changes / tests.
