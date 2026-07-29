#!/bin/bash

# Define paths
DB_PATH="storage/databases/pv.db"
LOG_PATH="storage/logs/uvicorn.log"
VECTOR_METADATA="storage/vector_metadata.pkl"
ENV_PATH=".env"

# 1. Load environment variables from .env if it exists
if [ -f "$ENV_PATH" ]; then
    echo "📜 Loading environment variables from $ENV_PATH..."
    # Export variables, ignoring comments and empty lines
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
    # Remove database
    if [ -f "$DB_PATH" ]; then
        rm "$DB_PATH"
        echo "   - Deleted SQLite Database"
    fi
    # Remove vector index metadata
    if [ -f "$VECTOR_METADATA" ]; then
        rm "$VECTOR_METADATA"
        echo "   - Deleted Vector Metadata"
    fi
    # Clear logs
    > "$LOG_PATH" || true
fi

echo "🚀 Igniting Intelligence Gateway..."
# Start uvicorn in the background
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