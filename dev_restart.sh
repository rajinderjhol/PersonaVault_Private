#!/bin/bash

# Define paths
DB_PATH="instance/personavault.db"
LOG_PATH="storage/logs/uvicorn.log"
VECTOR_METADATA="storage/vector_metadata.pkl"
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

# 2. Check for flags
SAFE_MODE=false
for arg in "$@"; do
  if [ "$arg" == "--safe" ] || [ "$arg" == "--soft" ]; then
    SAFE_MODE=true
  fi
done

echo "🛑 Stopping PersonaVault processes..."
pkill -f "uvicorn app.main:app" || true
pkill ollama 2>/dev/null || true
sleep 1

if [ "$SAFE_MODE" = true ]; then
    echo "🛡️  Safe Restart initiated. Preserving database and memory lattices..."
else
    echo "🔥 Full Restart initiated. Purging all volatile state..."
    if [ -f "$DB_PATH" ]; then
        rm "$DB_PATH"
        echo "   - Deleted SQLite Database"
    fi
    if [ -f "$VECTOR_METADATA" ]; then
        rm "$VECTOR_METADATA"
        echo "   - Deleted Vector Metadata"
    fi
    > "$LOG_PATH" || true
fi

# ============================================================
# 3. OLLAMA SETUP
# ============================================================
echo -e "${CYAN}🧠 Setting up Ollama...${NC}"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "  ${YELLOW}⚠️  Ollama not found. Installing...${NC}"
    
    # Check and install zstd if needed
    if ! command -v zstd &> /dev/null; then
        echo -e "  ${CYAN}   Installing zstd...${NC}"
        sudo apt-get update -qq
        sudo apt-get install zstd -y -qq
    fi
    
    curl -fsSL https://ollama.com/install.sh | sh
    echo -e "  ${GREEN}✅ Ollama installed.${NC}"
fi

# Start Ollama
echo -e "  ${CYAN}🚀 Starting Ollama...${NC}"
nohup ollama serve > ~/ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama
echo -ne "  ⏳ Waiting for Ollama to initialize..."
for i in {1..20}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e " ${GREEN}✅ Connected!${NC}"
        break
    fi
    echo -ne "."
    sleep 1
    if [ $i -eq 20 ]; then
        echo -e " ${YELLOW}⚠️  Timeout (continuing anyway)${NC}"
    fi
done

# Pull model if needed
MODEL="tinydolphin"
if command -v ollama &> /dev/null && curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "$MODEL"; then
    echo -e "  ${GREEN}✅ $MODEL model available.${NC}"
else
    echo -e "  ${CYAN}📥 Pulling $MODEL model (background)...${NC}"
    nohup ollama pull $MODEL > ~/ollama_pull.log 2>&1 &
fi

# ============================================================
# 4. DATABASE SETUP
# ============================================================
echo "🔧 Checking database tables..."
python3 -c "
import sqlite3
import os

DB_PATH = 'instance/personavault.db'
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS system_configs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('SELECT COUNT(*) FROM system_configs')
count = cursor.fetchone()[0]

if count == 0:
    print('   - Seeding default configuration...')
    groq_key = os.environ.get('GROQ_API_KEY', '')
    
    cursor.execute('''
    INSERT OR REPLACE INTO system_configs (key, value) VALUES 
        ('primary_ai_provider', 'groq'),
        ('ai_provider_groq_enabled', 'true'),
        ('ai_provider_groq_host', 'https://api.groq.com/openai/v1'),
        ('ai_provider_groq_model', 'llama-3.3-70b-versatile'),
        ('ai_provider_groq_api_key', ?),
        ('ai_provider_ollama_enabled', 'true'),
        ('ai_provider_ollama_host', 'http://localhost:11434')
    ''', (groq_key,))
    conn.commit()
    print('   - Default configuration seeded.')

conn.close()
print('✅ Database tables verified.')
"

# ============================================================
# 5. START SERVER
# ============================================================
export OLLAMA_HOST=http://localhost:11434
export PYTHONUNBUFFERED=1

echo "🚀 Igniting Intelligence Gateway..."
nohup python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > storage/logs/uvicorn.log 2>&1 &

UVICORN_PID=$!

# ============================================================
# 6. HEALTH CHECK (FIXED - Waits for Real Readiness)
# ============================================================
echo -e "${CYAN}⏳ Waiting for PersonaVault to be fully ready...${NC}"

MAX_WAIT=60
WAIT_COUNT=0
HEALTHY=false

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    # Check if uvicorn process is still running
    if ! pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo -e "\n  ${RED}❌ Uvicorn process died!${NC}"
        echo -e "  ${YELLOW}   Check: tail -20 storage/logs/uvicorn.log${NC}"
        exit 1
    fi
    
    # Check health endpoint
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health/engine 2>/dev/null)
    
    if echo "$HEALTH_RESPONSE" | grep -q '"status":"ready"'; then
        echo -e "\n  ${GREEN}✅ Engine is ready!${NC}"
        HEALTHY=true
        break
    fi
    
    # Show progress
    echo -ne "  ⏳ Waiting... ${WAIT_COUNT}/${MAX_WAIT}s\r"
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ "$HEALTHY" = false ]; then
    echo -e "\n  ${RED}❌ Engine failed to start within ${MAX_WAIT}s${NC}"
    echo -e "  ${YELLOW}   Check: tail -30 storage/logs/uvicorn.log${NC}"
    exit 1
fi

# ============================================================
# 7. DISPLAY SUMMARY
# ============================================================
echo ""
echo -e "${GREEN}${BOLD}✨ PersonaVault is now operational!${NC}"
echo "--------------------------------------------------"
echo "  Admin Dashboard:  http://localhost:8000/admin/dashboard"
echo "  API Swagger UI:   http://localhost:8000/docs"
echo "  Engine Health:    http://localhost:8000/health/engine"
echo "  Ollama PID:       $OLLAMA_PID"
echo "  Uvicorn PID:      $UVICORN_PID"
echo "--------------------------------------------------"
echo "Logs: tail -f storage/logs/uvicorn.log"
echo ""