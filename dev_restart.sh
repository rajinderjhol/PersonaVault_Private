#!/bin/bash
# Restart PersonaVault Backend

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check for --test flag to run suite before launch
RUN_TESTS=false
if [[ "$*" == *"--test"* ]]; then
    RUN_TESTS=true
fi

# Check for --soft flag to preserve database lattices and learned state
SOFT_RESTART=false
if [[ "$*" == *"--soft"* ]]; then
    SOFT_RESTART=true
fi

# Ensure core dependencies for vector search and ranking are installed in the venv
echo -e "${CYAN}⠿ Validating Python environment...${NC}"
if ! python -c "import faiss, rank_bm25, dotenv, verilink_plugin" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing/Updating missing libraries...${NC}"
    python -m pip install --upgrade pip
    python -m pip install faiss-cpu rank-bm25 python-dotenv verilink-aiverify-plugin --no-cache-dir
else
    echo -e "  ${GREEN}✅ All core dependencies present.${NC}"
fi

# ANSI color codes
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}♻️  PersonaVault: Recycling development environment...${NC}"
echo -e "${YELLOW}⏳ Releasing network ports and killing processes...${NC}"

# Silence job control and kill existing instances
set +m
sudo fuser -k 8000/tcp > /dev/null 2>&1 || true
pkill -9 -f "uvicorn.*app.main" > /dev/null 2>&1 || true
set -m

sleep 1

# Wait for port to be fully released to prevent "Address already in use" errors
echo -ne "⏳ Waiting for socket drainage..."
for i in {1..5}; do
    if ! (netstat -tuln | grep :8000 > /dev/null 2>&1 || lsof -i :8000 > /dev/null 2>&1); then
        break
    fi
    echo -ne "."
    sleep 1
done
echo -e " ${GREEN}✅${NC}"

if [ "$SOFT_RESTART" = true ]; then
    echo -e "${GREEN}⠿ Soft restart: Preserving existing database lattices and state.${NC}"
else
    # Re-initiate database for development to ensure schema consistency
    echo -e "${YELLOW}♻️  Re-initiating database lattices...${NC}"
    # Handle SQL Convergence vs Distributed strategy
    if [[ "$DATABASE_URL" == *"sqlite"* ]] || [ -z "$DATABASE_URL" ]; then
        rm -f storage/memory_db/personavault.db
        echo -e "${CYAN}⠿ Recycled SQLite file.${NC}"
    elif [[ "$DATABASE_URL" == *"postgres"* ]]; then
        echo -e "${CYAN}⠿ PostgreSQL lattice detected. Skipping file removal.${NC}"
        # Future: add logic to drop tables if 'full-recycle' flag is set
    fi

    # Reset vector store to ensure dimension consistency with current model
    # Only remove files if we aren't using a converged SQL engine (pgvector)
    if [ "$VECTOR_ENGINE" != "sql" ]; then
        rm -f storage/vector_index.faiss storage/vector_metadata.pkl
    fi
fi

# Maintenance: Clean common caches and truncate logs to prevent "Disk Full" errors in Cloud Shell
echo -e "${YELLOW}🧹 Maintenance: Purging caches and rotating logs...${NC}"
rm -rf ~/.cache/pip ~/.cache/npm ~/.cache/yarn 2>/dev/null || true
find storage/logs -name "*.log" -exec truncate -s 0 {} \; 2>/dev/null || true
truncate -s 0 ~/ollama.log 2>/dev/null || true
rm -rf ~/.ollama/models/blobs/*-partial 2>/dev/null || true

# Ensure storage and log directories exist
mkdir -p storage/logs storage/memory_db

# Leapfrog Quality Guardrail: Run tests if requested
if [ "$RUN_TESTS" = true ]; then
    echo -e "${CYAN}🧪 Running Cognitive Guardrail Tests...${NC}"
    if ! pytest tests/ -v; then
        echo -e "${YELLOW}❌ Tests failed. Aborting restart to prevent unstable deployment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Tests passed. Proceeding with ignition.${NC}"
fi

# Ensure AI models are pulled and ready BEFORE the server is declared operational
if [ -f "../scripts/setup_ollama.sh" ]; then
    echo -e "${CYAN}⠿ Preparing AI Engine (Ollama)...${NC}"
    bash ../scripts/setup_ollama.sh
fi

# Define a cleanup function to kill the new server if the script is interrupted
cleanup() {
    echo -e "\n${NC}${YELLOW}🛑 Interrupted. Cleaning up server process...${NC}"
    if [ ! -z "$UVICORN_PID" ]; then
        kill $UVICORN_PID > /dev/null 2>&1 || true
    fi
    exit
}
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}✅ Cleaned. Starting new instance...${NC}"
echo -e "${CYAN}🚀 Launching PersonaVault Backend (Modern Async)${NC}"

export PYTHONUNBUFFERED=1
export PYTHONPATH=$PYTHONPATH:$(pwd)
# Start uvicorn in the background (&) to keep the terminal responsive.
# We do NOT use 'exec' so that the shell script returns control to you.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info > storage/logs/uvicorn.log 2>&1 &
UVICORN_PID=$!

echo -ne "⏳ Waiting for cognitive engine ignition (Timeout: 60s)..."
counter=0
# Use the logical health check for robust verification instead of log grepping
# Accept 'ready' (full connectivity) or 'degraded' (logic is up but some AI services are offline)
until curl -s http://localhost:8000/health/engine | grep -qE '"status":"(ready|degraded)"'; do
    if ! ps -p $UVICORN_PID > /dev/null; then
        echo -e "\n${NC}\033[1;31m❌ Process died. Check terminal for error trace below:${NC}"
        cat storage/logs/uvicorn.log
        exit 1
    fi
    if [ $counter -ge 60 ]; then
        echo -e "\n${NC}\033[1;33m⚠️  Ignition timeout. Logic initialization taking longer than expected.${NC}"
        tail -n 20 storage/logs/uvicorn.log
        exit 1
    fi
    echo -ne "."
    sleep 1
    ((counter++))
done
echo -e " ${GREEN}✅ Ready!${NC}"

# Display summary from the actual logs
echo -e "\n"
grep "✨ PersonaVault" -A 10 storage/logs/uvicorn.log