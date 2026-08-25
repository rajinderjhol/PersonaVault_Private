#!/bin/bash

# Define paths
DB_PATH="storage/memory_db/personavault.db"
LOG_PATH="storage/logs/uvicorn.log"
ENV_PATH=".env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 1. Load environment variables from .env if it exists
if [ -f "$ENV_PATH" ]; then
    echo "📜 Loading environment variables from $ENV_PATH..."
    export $(grep -v '^#' "$ENV_PATH" | xargs)
fi

# Check for --safe flag
PURGE_STATE=true
if [ "$1" == "--safe" ]; then
    echo "🛡️ Safe mode detected: Skipping volatile state purge."
    PURGE_STATE=false
fi

echo "🛑 Stopping PersonaVault processes..."
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "ollama" 2>/dev/null || true
sleep 2

# Purge volatile state if --force flag is used
if [ "$1" == "--force" ]; then
    echo "🔥 Forced Restart initiated. Purging all volatile state..."
    rm -f "$DB_PATH"
    > "$LOG_PATH"
elif [ -f "$DB_PATH" ]; then
    echo "✅ Database found at $DB_PATH. Skipping purge and seeding."
    PURGE_STATE=false
else
    echo "🔥 No database found. Running full initialization..."
    PURGE_STATE=true
fi

# 2. OLLAMA SETUP
echo -e "${CYAN}🧠 Setting up Ollama...${NC}"
# Check for zstd
if ! command -v zstd &> /dev/null; then
    echo "⚠️ zstd not found, installing..."
    sudo apt-get update && sudo apt-get install -y zstd
fi
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
nohup ollama serve > ~/ollama.log 2>&1 &
export OLLAMA_HOST=http://localhost:11434
echo -ne "  ⏳ Waiting for Ollama..."
for i in {1..20}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e " ${GREEN}✅ Connected!${NC}"
        break
    fi
    echo -ne "."
    sleep 1
done

# 3. DATABASE SETUP
if [ "$PURGE_STATE" = true ]; then
    echo "🔧 Initializing database schema..."
    export PYTHONPATH=$PWD
    python3 -c "
from app.db.session import engine, Base
import asyncio
import app.models
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init_db())
"

    echo "🌱 Running data seeding..."
    python3 scripts/seed_all_data.py
    python3 scripts/install_all_packs.py
    python3 scripts/seed_contract_memories.py
else
    echo "ℹ️ Skipping database initialization and seeding."
fi

# 4. START SERVER
echo "🚀 Igniting Intelligence Gateway..."
export PYTHONPATH=$PWD
nohup python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    > "$LOG_PATH" 2>&1 &

# 5. HEALTH CHECK
echo -e "${CYAN}⏳ Waiting for PersonaVault...${NC}"
for i in {1..60}; do
    if curl -s http://localhost:8000/health/engine | grep -q '"status":"ready"'; then
        echo -e "\n  ${GREEN}✅ Engine is ready!${NC}"
        break
    fi
    echo -ne "  ⏳ Waiting... ${i}/60s\r"
    sleep 1
done

echo ""
echo -e "${GREEN}${BOLD}✨ PersonaVault is now operational!${NC}"
echo "--------------------------------------------------"
echo "  Admin Dashboard:  http://localhost:8000/admin/dashboard"
echo "  API Swagger UI:   http://localhost:8000/docs"
echo "  Health Monitor:   http://localhost:8000/health/detailed"
echo "--------------------------------------------------"
echo "Logs: tail -f $LOG_PATH"
