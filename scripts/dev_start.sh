#!/bin/bash
# Start PersonaVault Backend in Development Mode - Cloud Shell Optimized

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

echo -e "${CYAN}${BOLD}┌──────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}${BOLD}│ 🚀 Launching PersonaVault Backend (Cloud Shell) │${NC}"
echo -e "${CYAN}${BOLD}└──────────────────────────────────────────────────┘${NC}"

# ============================================================
# 1. DIRECTORY SETUP
# ============================================================
mkdir -p storage/logs storage/memory_db
echo -e "${CYAN}⠿ Validating Local-First Infrastructure...${NC}"

# ============================================================
# 2. OLLAMA DETECTION & VERIFICATION
# ============================================================
if curl -s -m 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Local AI (Ollama) detected.${NC}"
    
    # Check if tinydolphin is pulled (Cloud Shell optimized)
    if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "tinydolphin"; then
        echo -e "  ${GREEN}✅ tinydolphin model ready.${NC}"
    else
        echo -e "  ${YELLOW}⚠️  tinydolphin model not found. Pulling...${NC}"
        ollama pull tinydolphin &
        PULL_PID=$!
        echo -e "  ${CYAN}   Pulling in background (PID: $PULL_PID)${NC}"
        echo -e "  ${CYAN}   Run 'tail -f ~/ollama.log' to monitor progress${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  Ollama not responding. Starting in background...${NC}"
    ollama serve > ~/ollama.log 2>&1 &
    echo -e "  ${CYAN}   Ollama PID: $!${NC}"
    echo -e "  ${CYAN}   Waiting for Ollama to initialize...${NC}"
    sleep 3
    echo -e "  ${GREEN}✅ Ollama started.${NC}"
fi

# ============================================================
# 3. NEO4J DETECTION (Cloud Shell - Usually unavailable)
# ============================================================
if timeout 1 bash -c "</dev/tcp/localhost/7687" 2>/dev/null; then
    echo -e "  ${GREEN}✅ Local Graph Service (Neo4j) detected.${NC}"
else
    echo -e "  ${CYAN}⠿ Local Graph (Neo4j) not available. Using SQL simulation.${NC}"
fi

# ============================================================
# 4. DISK SPACE CHECK (Cloud Shell Critical)
# ============================================================
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//' 2>/dev/null)
if [ -n "$DISK_USAGE" ] && [ "$DISK_USAGE" -gt 85 ]; then
    echo -e "  ${RED}⚠️  DISK SPACE WARNING: ${DISK_USAGE}% used${NC}"
    echo -e "  ${YELLOW}   Run: ./dev_restart.sh --soft (or manually clean cache)${NC}"
fi

# ============================================================
# 5. DEPENDENCY VALIDATION
# ============================================================
echo -e "${CYAN}⠿ Validating core dependencies...${NC}"
MISSING_DEPS=""
for dep in faiss rank_bm25 dotenv passlib bcrypt; do
    if ! python -c "import $dep" &>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $dep"
    fi
done

if [ -n "$MISSING_DEPS" ]; then
    echo -e "  ${YELLOW}⚠️  Missing dependencies:$MISSING_DEPS${NC}"
    echo -e "  ${CYAN}   Installing...${NC}"
    python -m pip install --upgrade pip --no-cache-dir
    python -m pip install faiss-cpu rank-bm25 python-dotenv passlib bcrypt==4.0.1 --no-cache-dir
    echo -e "  ${GREEN}✅ Dependencies installed.${NC}"
else
    echo -e "  ${GREEN}✅ All core dependencies present.${NC}"
fi

# ============================================================
# 6. STARTUP MESSAGE
# ============================================================
echo -e "${CYAN}⠿ Logs: ${BOLD}storage/logs/uvicorn.log${NC}"
echo -e "${CYAN}⠿ Tail: ${BOLD}tail -f storage/logs/uvicorn.log${NC}"

# Set Cloud Shell optimizations
export PYTHONUNBUFFERED=1
export PYTHONPATH=$PYTHONPATH:$(pwd)
export OLLAMA_BATCH_SIZE=5
export MAX_MEMORY_ENTRIES=50

# ============================================================
# 7. LAUNCH SERVER (Without exec - allows cleanup)
# ============================================================
echo -e "${GREEN}${BOLD}✨ Launching PersonaVault...${NC}"

python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    > storage/logs/uvicorn.log 2>&1 &

UVICORN_PID=$!

# ============================================================
# 8. HEALTH CHECK
# ============================================================
echo -ne "⏳ Waiting for engine to initialize..."
counter=0
MAX_WAIT=60

until curl -s http://localhost:8000/health/engine 2>/dev/null | grep -qE '"status":"(ready|degraded)"'; do
    if ! ps -p $UVICORN_PID > /dev/null 2>&1; then
        echo -e "\n${RED}❌ Process died. Check logs:${NC}"
        tail -n 20 storage/logs/uvicorn.log
        exit 1
    fi
    if [ $counter -ge $MAX_WAIT ]; then
        echo -e "\n${YELLOW}⚠️  Timeout. Engine may still be initializing.${NC}"
        echo -e "${YELLOW}   Check logs: tail -f storage/logs/uvicorn.log${NC}"
        break
    fi
    echo -ne "."
    sleep 1
    ((counter++))
done

# ============================================================
# 9. DISPLAY SUMMARY
# ============================================================
echo -e "\n${GREEN}${BOLD}✨ PersonaVault is now operational!${NC}"
echo -e "${CYAN}--------------------------------------------------${NC}"
echo -e "  ${BOLD}Admin Dashboard:${NC}  http://localhost:8000/admin/dashboard"
echo -e "  ${BOLD}API Swagger UI:${NC}   http://localhost:8000/docs"
echo -e "  ${BOLD}Engine Health:${NC}    http://localhost:8000/health/engine"
echo -e "  ${BOLD}Process PID:${NC}      $UVICORN_PID"
echo -e "${CYAN}--------------------------------------------------${NC}"

# Show disk usage if near limit
if [ -n "$DISK_USAGE" ] && [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${YELLOW}⚠️  Disk usage: ${DISK_USAGE}% (consider cleanup)${NC}"
fi

echo -e "${CYAN}💡 Stop server: kill $UVICORN_PID${NC}"
echo -e "${CYAN}💡 View logs: tail -f storage/logs/uvicorn.log${NC}"
echo ""