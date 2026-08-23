#!/bin/bash
# CLI Integration Test Suite for PersonaVault

PV_BIN="./cli/pv"
export PV_USERNAME="admin"
export PV_PASSWORD="admin123"

echo "🚀 Starting CLI Integration Tests..."

# 1. Test Chat
echo "Testing: pv chat..."
RESPONSE=$($PV_BIN chat "test message" --provider ollama)
if [[ $? -eq 0 ]]; then
    echo "✅ pv chat successful"
else
    echo "❌ pv chat failed"
    exit 1
fi

# 2. Test Decide
echo "Testing: pv decide..."
# The behavior endpoint expects event_type and outcome, now handled by CLI defaults
DECISION_OUT=$($PV_BIN decide --domain "cli_test" --decision "logged" --reason "CLI Integration Test")
if [[ $? -eq 0 ]]; then
    echo "✅ pv decide successful"
    echo "$DECISION_OUT" | grep -q "id"
    if [[ $? -eq 0 ]]; then
        echo "   -> Decision ID found in output"
    fi
else
    echo "❌ pv decide failed"
    echo "Output: $DECISION_OUT"
    exit 1
fi

# 3. Test Trends
echo "Testing: pv trends..."
TRENDS_OUT=$($PV_BIN trends --days 1)
if [[ $? -eq 0 ]]; then
    echo "✅ pv trends successful"
else
    echo "❌ pv trends failed"
    exit 1
fi

echo "🏆 All CLI Integration Tests Passed!"
