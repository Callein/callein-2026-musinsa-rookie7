# CLAUDE.md - AI Agent Instructions

## Project Overview

대학교 수강신청 시스템 백엔드 API (Python + FastAPI + PostgreSQL)

## Tech Stack

- Python 3.11+, FastAPI, Uvicorn
- PostgreSQL (asyncpg), SQLAlchemy 2.0 (async)
- JWT authentication (PyJWT + passlib/bcrypt)
- Docker Compose for PostgreSQL

## Project Structure

```
src/
├── main.py              # FastAPI app entry point with lifespan
├── config.py            # Environment configuration
├── database.py          # Async SQLAlchemy engine and session
├── dependencies.py      # FastAPI dependencies (get_db, get_current_student)
├── models/              # SQLAlchemy ORM models
├── routers/             # API endpoint handlers
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic layer
└── utils/               # Seed data tokens
tests/                   # pytest test files
docs/                    # API docs, requirements analysis
.bruno/                  # Bruno API collection
```

## Key Design Decisions

1. **Concurrency Control**: PostgreSQL `SELECT FOR UPDATE` row-level locking
   - Single course per enrollment request → no deadlock risk
   - Read Committed isolation level is sufficient
2. **Authentication**: JWT Bearer token for enrollment/drop/schedule APIs
3. **Error Codes**: 409 Conflict for enrollment failures (capacity, credits, schedule conflict)
4. **Data Seeding**: Idempotent (skips if data exists), deterministic (seed=42)

## Development Commands

```bash
# Start PostgreSQL
docker compose up -d

# Install dependencies
pip install -r requirements.txt

# Run server
python src/main.py

# Run tests
pytest --cov=src

# Health check
curl http://127.0.0.1:8000/health
```

## Coding Conventions

- Immutable patterns: create new objects instead of mutation
- Type hints on all functions
- snake_case for files/functions, PascalCase for classes
- Functions < 50 lines, files < 800 lines
- Pydantic v2: use `ConfigDict(from_attributes=True)`
- Error messages in Korean (user-facing)

## Git Workflow

- Branch naming: `feature/기능명`, `fix/버그명`
- Commit format: `type(scope): description` in English
- Types: feat, fix, docs, style, refactor, perf, test, chore
- Commit per concern, not bulk commits
- Phase-based branches for PRs

## API Response Format

All APIs must follow a consistent response format:

**List endpoints (paginated):**
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "total": 10000,
    "page": 1,
    "limit": 20,
    "total_pages": 500
  }
}
```

**Single resource endpoints:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error responses:**
```json
{
  "success": false,
  "error": "사용자 친화적 에러 메시지"
}
```

**HTTP status codes:**
- 200: Success
- 201: Created (enrollment)
- 400: Bad Request (invalid input)
- 401: Unauthorized (missing/invalid JWT)
- 404: Not Found (resource does not exist)
- 409: Conflict (capacity full, credit limit, schedule conflict, duplicate enrollment)
- 422: Validation Error (FastAPI automatic)

## API Base URL

- Health: `GET /health`
- All other APIs: `/api/...` prefix
- Bruno environment: `BASE_URL=http://127.0.0.1:8000/api`
