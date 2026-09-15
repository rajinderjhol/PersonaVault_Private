#!/usr/bin/env bash
set -euo pipefail

# 1. Python venv
if [ ! -d .venv ]; then
  echo "→ Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# 2. Dependencies
if [ ! -f .venv/.deps-installed ]; then
  echo "→ Installing Python dependencies..."
  pip install -r requirements.txt
  touch .venv/.deps-installed
fi

# 3. Postgres container
if ! docker ps --format '{{.Names}}' | grep -q personavault-postgres; then
  if docker ps -a --format '{{.Names}}' | grep -q personavault-postgres; then
    echo "→ Starting existing Postgres container..."
    docker start personavault-postgres
  else
    echo "→ Creating new Postgres container..."
    docker run -d \
      --name personavault-postgres \
      -e POSTGRES_USER=personavault \
      -e POSTGRES_PASSWORD=personavault \
      -e POSTGRES_DB=personavault \
      -p 5432:5432 \
      -v personavault-pgdata:/var/lib/postgresql/data \
      postgres:16
  fi
fi

# Wait for Postgres to be ready
echo "→ Waiting for Postgres..."
for i in $(seq 1 30); do
  if docker exec personavault-postgres pg_isready -U personavault > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

# 4. .env setup
if [ ! -f .env ]; then
  echo "→ Creating .env from .env.example..."
  cp .env.example .env
fi

# 5. Start the app
echo "→ Starting PersonaVault..."
./scripts/dev_restart.sh
