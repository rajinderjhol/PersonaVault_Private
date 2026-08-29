#!/bin/bash
# Run all identity tests

echo "🧪 Running Identity Layer Tests"
echo "================================"

# Check if server is running
if ! curl -s http://localhost:8000/health/engine > /dev/null 2>&1; then
    echo "⚠️ Server is not running. Waiting for startup..."
    for i in {1..120}; do
        if curl -s http://localhost:8000/health/engine > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    if ! curl -s http://localhost:8000/health/engine > /dev/null 2>&1; then
        echo "⚠️ Server failed to start."
        exit 1
    fi
fi

# Run service tests
echo ""
echo "📋 Running Service Tests..."
cd ~/personavault/backend
./.venv/bin/python tests/test_identity_service.py

# Run API tests
echo ""
echo "📋 Running API Tests..."
./.venv/bin/python tests/test_identity_api.py

echo ""
echo "✅ Identity Tests Complete"
