#!/bin/bash

# Define paths
DB_PATH="instance/personavault.db"
LOG_PATH="storage/logs/uvicorn.log"
VECTOR_METADATA="storage/vector_metadata.pkl"
ENV_PATH=".env"

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

# 3. Ensure system_configs table exists (for AI provider settings)
echo "🔧 Checking database tables..."
python3 -c "
import sqlite3
import os

DB_PATH = 'instance/personavault.db'

# Ensure directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create system_configs table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS system_configs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Check if we need to seed default configs
cursor.execute('SELECT COUNT(*) FROM system_configs')
count = cursor.fetchone()[0]

if count == 0:
    print('   - Seeding default configuration...')
    # Check if GROQ_API_KEY is in environment
    groq_key = os.environ.get('GROQ_API_KEY', '')
    
    cursor.execute('''
    INSERT OR REPLACE INTO system_configs (key, value) VALUES 
        ('primary_ai_provider', 'groq'),
        ('ai_provider_groq_enabled', 'true'),
        ('ai_provider_groq_host', 'https://api.groq.com/openai/v1'),
        ('ai_provider_groq_model', 'llama-3.3-70b-versatile'),
        ('ai_provider_groq_api_key', ?)
    ''', (groq_key,))
    conn.commit()
    print('   - Default configuration seeded.')

conn.close()
print('✅ Database tables verified.')
"

echo "🚀 Igniting Intelligence Gateway..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > storage/logs/uvicorn.log 2>&1 &

echo "✅ Restart complete. Mode: $( [ "$SAFE_MODE" = true ] && echo "Safe (Data Preserved)" || echo "Full Wipe" )"
echo ""
echo "✨ PersonaVault is now operational!"
echo "--------------------------------------------------"
echo "  Admin Dashboard:  http://localhost:8000/admin/dashboard"
echo "  API Swagger UI:   http://localhost:8000/docs"
echo "  Engine Health:    http://localhost:8000/health/engine"
echo "--------------------------------------------------"
echo "Logs: tail -f storage/logs/uvicorn.log"
