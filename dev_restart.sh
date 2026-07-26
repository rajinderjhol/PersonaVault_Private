#!/bin/bash
# Restart PersonaVault Backend - Cloud Shell Optimized

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Parse arguments
RUN_TESTS=false
SOFT_RESTART=false
SKIP_OLLAMA=false
for arg in "$@"; do
    case $arg in
        --test) RUN_TESTS=true ;;
        --soft) SOFT_RESTART=true ;;
        --skip-ollama) SKIP_OLLAMA=true ;;
    esac
done

echo -e "${CYAN}${BOLD}♻️  PersonaVault: Recycling development environment...${NC}"

# ============================================================
# 1. ENVIRONMENT VALIDATION (Cloud Shell specific)
# ============================================================
echo -e "${CYAN}⠿ Validating Python environment...${NC}"
if ! python -c "import faiss, rank_bm25, dotenv, passlib, bcrypt" &> /dev/null; then
    echo -e "${YELLOW}📦 Installing/Updating missing libraries...${NC}"
    python -m pip install --upgrade pip --no-cache-dir
    python -m pip install faiss-cpu rank-bm25 python-dotenv passlib bcrypt==4.0.1 --no-cache-dir
else
    echo -e "  ${GREEN}✅ All core dependencies present.${NC}"
fi

# ============================================================
# 2. PORT CLEANUP (Cloud Shell compatible - no sudo)
# ============================================================
echo -e "${YELLOW}⏳ Releasing network ports...${NC}"

# Cloud Shell doesn't have sudo, use fuser without sudo
if command -v fuser &> /dev/null; then
    fuser -k 8000/tcp > /dev/null 2>&1 || true
else
    # Fallback: kill by process name
    pkill -9 -f "uvicorn.*app.main" > /dev/null 2>&1 || true
    pkill -9 -f "python.*app.main" > /dev/null 2>&1 || true
fi

# Additional cleanup: kill any hanging Python processes
pkill -9 -f "uvicorn" > /dev/null 2>&1 || true
pkill -9 -f "python.*main" > /dev/null 2>&1 || true

sleep 1

# Wait for port to be fully released
echo -ne "⏳ Waiting for socket drainage..."
for i in {1..5}; do
    if ! (netstat -tuln 2>/dev/null | grep :8000 > /dev/null 2>&1 || lsof -i :8000 2>/dev/null > /dev/null 2>&1); then
        break
    fi
    echo -ne "."
    sleep 1
done
echo -e " ${GREEN}✅${NC}"

# ============================================================
# 3. DATABASE STATE MANAGEMENT
# ============================================================
if [ "$SOFT_RESTART" = true ]; then
    echo -e "${GREEN}⠿ Soft restart: Preserving database and learned state.${NC}"
else
    echo -e "${YELLOW}♻️  Re-initiating database lattices...${NC}"
    
    # Check if using SQLite (Cloud Shell default)
    if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == *"sqlite"* ]]; then
        rm -f storage/memory_db/personavault.db
        echo -e "${CYAN}⠿ Recycled SQLite database.${NC}"
    fi

    # Reset FAISS vector store (only if not using converged SQL)
    if [ "$VECTOR_ENGINE" != "sql" ]; then
        rm -f storage/vector_index.faiss storage/vector_metadata.pkl
        echo -e "${CYAN}⠿ Recycled FAISS vector index.${NC}"
    fi
fi

# ============================================================
# 4. CACHE CLEANUP (Cloud Shell disk space preservation)
# ============================================================
echo -e "${YELLOW}🧹 Maintenance: Purging caches...${NC}"

# Check disk space before cleanup
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${YELLOW}⚠️  Disk usage is at ${DISK_USAGE}%. Cleaning aggressively...${NC}"
    
    # Aggressive cleanup when disk is full
    rm -rf ~/.cache/pip/* 2>/dev/null || true
    rm -rf ~/.cache/npm/* 2>/dev/null || true
    rm -rf ~/.cache/yarn/* 2>/dev/null || true
    rm -rf ~/.ollama/models/blobs/*-partial 2>/dev/null || true
fi

# Always truncate logs to prevent growth
find storage/logs -name "*.log" -exec truncate -s 0 {} \; 2>/dev/null || true
truncate -s 0 ~/ollama.log 2>/dev/null || true

# Ensure directories exist
mkdir -p storage/logs storage/memory_db

# ============================================================
# 5. OLLAMA SETUP (Cloud Shell optimized)
# ============================================================
if [ "$SKIP_OLLAMA" = false ] && [ -f "../scripts/setup_ollama.sh" ]; then
    echo -e "${CYAN}⠿ Preparing AI Engine (Ollama)...${NC}"
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Ollama not running. Starting in background...${NC}"
        ollama serve > /dev/null 2>&1 &
        sleep 2
    fi
    
    # Check if tinydolphin is pulled
    if ! curl -s http://localhost:11434/api/tags | grep -q "tinydolphin"; then
        echo -e "${YELLOW}📦 Pulling tinydolphin model (Cloud Shell optimized)...${NC}"
        ollama pull tinydolphin
    else
        echo -e "  ${GREEN}✅ tinydolphin model ready.${NC}"
    fi
    
    bash ../scripts/setup_ollama.sh
fi

# ============================================================
# 6. TEST GUARDRAIL
# ============================================================
if [ "$RUN_TESTS" = true ]; then
    echo -e "${CYAN}🧪 Running Cognitive Guardrail Tests...${NC}"
    if ! pytest tests/ -v --tb=short; then
        echo -e "${RED}❌ Tests failed. Aborting restart.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Tests passed. Proceeding with ignition.${NC}"
fi

# ============================================================
# 7. LAUNCH SERVER
# ============================================================
echo -e "${GREEN}✅ Cleaned. Starting new instance...${NC}"
echo -e "${CYAN}🚀 Launching PersonaVault Backend (Cloud Shell Optimized)${NC}"

# Set Python path and environment
export PYTHONUNBUFFERED=1
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Cloud Shell specific: reduce memory usage
export OLLAMA_BATCH_SIZE=5
export MAX_MEMORY_ENTRIES=50

# Start uvicorn in background
python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    > storage/logs/uvicorn.log 2>&1 &
UVICORN_PID=$!

# ============================================================
# 8. HEALTH CHECK (Cloud Shell optimized)
# ============================================================
echo -ne "⏳ Waiting for cognitive engine ignition (Timeout: 90s)..."
counter=0
MAX_WAIT=90

until curl -s http://localhost:8000/health/engine | grep -qE '"status":"(ready|degraded)"' 2>/dev/null; do
    if ! ps -p $UVICORN_PID > /dev/null 2>&1; then
        echo -e "\n${RED}❌ Process died. Check logs:${NC}"
        tail -n 30 storage/logs/uvicorn.log
        exit 1
    fi
    
    # Check for common Cloud Shell issues
    if [ $counter -eq 30 ]; then
        echo -e "\n${YELLOW}⚠️  Taking longer than expected. Checking Ollama...${NC}"
        if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo -e "${RED}❌ Ollama is not responding. Please start Ollama separately.${NC}"
        fi
    fi
    
    if [ $counter -ge $MAX_WAIT ]; then
        echo -e "\n${RED}❌ Ignition timeout. Last 20 log lines:${NC}"
        tail -n 20 storage/logs/uvicorn.log
        exit 1
    fi
    
    echo -ne "."
    sleep 1
    ((counter++))
done

echo -e " ${GREEN}✅ Ready!${NC}"

# ============================================================
# 9. DISPLAY SUMMARY
# ============================================================
echo -e "\n${GREEN}${BOLD}✨ PersonaVault is now operational!${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e "  ${BOLD}Admin Dashboard:${NC}  http://localhost:8000/admin/dashboard"
echo -e "  ${BOLD}API Swagger UI:${NC}   http://localhost:8000/docs"
echo -e "  ${BOLD}Engine Health:${NC}    http://localhost:8000/health/engine"
echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e "${YELLOW}Logs: tail -f storage/logs/uvicorn.log${NC}"

# Display disk usage warning if needed
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo -e "\n${RED}⚠️  DISK SPACE WARNING: ${DISK_USAGE}% used${NC}"
    echo -e "${YELLOW}   Run cleanup: rm -rf ~/.cache/* ~/.ollama/models/blobs/*-partial${NC}"
fi

echo ""