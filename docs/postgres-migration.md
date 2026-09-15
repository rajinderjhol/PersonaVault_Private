# PostgreSQL Migration Guide

This document details the transition from SQLite to PostgreSQL for the PersonaVault backend.

## Why PostgreSQL?
While SQLite was suitable for early development, PostgreSQL provides:
- Robust support for concurrent writes and complex queries.
- Strict data type enforcement and constraints, improving reliability.
- Advanced features like JSONB for efficient unstructured data storage.
- Consistency between development (Docker/Postgres) and production environments.

## What Changed
### 1. Database Engine
- Switched from `sqlite:///./instance/database.db` to `postgresql+asyncpg://personavault:personavault@localhost:5432/personavault`.
- Utilizes `SQLAlchemy`'s `AsyncEngine` with `NullPool` for tests to ensure proper connection lifecycle management.

### 2. Model Adjustments
- Updated `DateTime` fields to `DateTime(timezone=True)` for accurate temporal handling.
- Converted `UUID` primary keys to `Integer` (or appropriate Postgres-native types where necessary).
- Implemented `JSONB` instead of `JSON` for better indexing and query performance.
- Adjusted boolean handling to be strictly compatible with Postgres' `BOOLEAN` type.

### 3. Test Infrastructure
- Refactored test fixtures in `tests/conftest.py` to use a fresh `AsyncSession` per test/request, resolving test isolation issues caused by shared sessions.
- Ensured all asynchronous calls in the test suite are properly `await`-ed.

## How to Run Locally

### 1. Requirements
- Docker and Docker Compose installed.

### 2. Start PostgreSQL
Run the following to start a persistent Postgres container:
```bash
docker run -d \
  --name personavault-postgres \
  -e POSTGRES_USER=personavault \
  -e POSTGRES_PASSWORD=personavault \
  -e POSTGRES_DB=personavault \
  -p 5432:5432 \
  -v personavault-pgdata:/var/lib/postgresql/data \
  postgres:16
```

### 3. Initialize & Restart
Use the provided script to initialize the database and start the app:
```bash
./scripts/dev_restart.sh
```

## Differences from SQLite
- **Strict Typing**: PostgreSQL will raise errors for type mismatches that SQLite might have silently cast.
- **Case Sensitivity**: Identifiers (table/column names) are case-sensitive if quoted, but generally lowercase by default in Postgres.
- **Date Handling**: Strictly enforced timezone compliance via `timestamptz`.
