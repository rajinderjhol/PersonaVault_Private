#!/bin/bash
# Start PersonaVault Backend in Development Mode

# Navigate to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# ANSI color codes
CYAN='\033[1;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}┌──────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}${BOLD}│ 🚀 Launching PersonaVault Backend (Modern Async) │${NC}"
echo -e "${CYAN}${BOLD}└──────────────────────────────────────────────────┘${NC}"

mkdir -p storage/logs storage/memory_db
echo -e "${CYAN}⠿ Validating Local-First Infrastructure...${NC}"

# Pre-flight check for Ollama (Local AI)
if curl -s -m 2 http://localhost:11434/api/tags > /dev/null; then
    echo -e "  ${GREEN}✅ Local AI (Ollama) detected.${NC}"
else
    echo -e "  ${YELLOW}⚠️  Local AI not found. Ready for Cloud (Gemini) fallback.${NC}"
fi

# Pre-flight check for Neo4j (Local Graph)
if timeout 1 bash -c "</dev/tcp/localhost/7687" 2>/dev/null; then
    echo -e "  ${GREEN}✅ Local Graph Service (Neo4j) detected.${NC}"
else
    echo -e "  ${YELLOW}⚠️  Local Graph (Neo4j) not detected on bolt port.${NC}"
fi

echo -e "${CYAN}⠿ Logs are being redirected to: ${BOLD}storage/logs/uvicorn.log${NC}"
echo -e "${CYAN}⠿ Use 'tail -f storage/logs/uvicorn.log' in another tab to view.${NC}"

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level warning > storage/logs/uvicorn.log 2>&1