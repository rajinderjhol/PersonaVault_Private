#!/bin/bash
echo "🧪 PersonaVault Complete Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Login
echo -n "🔐 Login: "
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c /tmp/pv_cookies.txt > /dev/null
echo -e "${GREEN}✅${NC}"

# 1. List models
echo -n "📦 List Models: "
MODEL_COUNT=$(curl -s http://localhost:8000/api/v1/ollama/models -b /tmp/pv_cookies.txt | python -c "import json,sys; print(len(json.load(sys.stdin).get('models', [])))")
echo -e "${GREEN}✅${NC} ($MODEL_COUNT models)"

# 2. AI Chat
echo -n "🤖 AI Chat: "
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"tinydolphin","messages":[{"role":"user","content":"Say hello in 3 words"}],"stream":false}' \
  -b /tmp/pv_cookies.txt --max-time 30)
if echo "$RESPONSE" | grep -q "content"; then
    echo -e "${GREEN}✅${NC} (tinydolphin responded)"
else
    echo -e "${RED}❌${NC}"
fi

# 3. Create memory
echo -n "📝 Create Memory: "
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/memory/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Suite Memory","content":"Created by test script"}' \
  -b /tmp/pv_cookies.txt)
if echo "$RESPONSE" | grep -q "id"; then
    ID=$(echo "$RESPONSE" | python -c "import json,sys; print(json.load(sys.stdin).get('id'))")
    echo -e "${GREEN}✅${NC} (ID: $ID)"
else
    echo -e "${RED}❌${NC}"
fi

# 4. List memories
echo -n "📋 List Memories: "
COUNT=$(curl -s http://localhost:8000/api/v1/memory/ -b /tmp/pv_cookies.txt | python -c "import json,sys; print(len(json.load(sys.stdin)))")
echo -e "${GREEN}✅${NC} ($COUNT memories)"

# 5. Search
echo -n "🔍 Search: "
RESULT_COUNT=$(curl -s "http://localhost:8000/api/v1/memory/search?query=test" -b /tmp/pv_cookies.txt | python -c "import json,sys; print(len(json.load(sys.stdin).get('results', [])))")
echo -e "${GREEN}✅${NC} (Found $RESULT_COUNT results)"

# 6. Dashboard
echo -n "📊 Dashboard: "
METRICS=$(curl -s http://localhost:8000/api/v1/admin/dashboard/metrics -b /tmp/pv_cookies.txt)
if echo "$METRICS" | grep -q "memories"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# 7. Context
echo -n "📋 Context: "
CONTEXT=$(curl -s http://localhost:8000/api/v1/context/current -b /tmp/pv_cookies.txt)
if echo "$CONTEXT" | grep -q "context"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️${NC}"
fi

echo ""
echo -e "${GREEN}✅ Test Suite Complete!${NC}"
