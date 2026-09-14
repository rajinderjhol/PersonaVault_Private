#!/bin/bash
echo "🧪 Testing PersonaVault API..."
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

# 1. Create Memory
echo -n "📝 Create Memory: "
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/memory/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Memory","content":"PersonaVault API test successful!"}' \
  -b /tmp/pv_cookies.txt)
if echo "$RESPONSE" | grep -q '"id"'; then
    echo -e "${GREEN}✅${NC}"
    echo "   Created: $(echo $RESPONSE | python -m json.tool | grep '"title"' | head -1)"
else
    echo -e "${RED}❌${NC}"
    echo "   Error: $RESPONSE"
fi

# 2. Search Memory
echo -n "🔍 Search Memory: "
RESPONSE=$(curl -s "http://localhost:8000/api/v1/memory/search?query=PersonaVault" \
  -b /tmp/pv_cookies.txt)
if echo "$RESPONSE" | grep -q '"results"'; then
    COUNT=$(echo "$RESPONSE" | python -c "import json,sys; print(len(json.load(sys.stdin).get('results', [])))")
    echo -e "${GREEN}✅${NC} (Found $COUNT results)"
else
    echo -e "${YELLOW}⚠️${NC} (No results yet)"
fi

# 3. Ollama Chat
echo -n "🤖 Ollama Chat: "
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"What is PersonaVault?"}' \
  -b /tmp/pv_cookies.txt)
if echo "$RESPONSE" | grep -q '"response"'; then
    echo -e "${GREEN}✅${NC}"
    echo "   Response: $(echo $RESPONSE | python -c "import json,sys; print(json.load(sys.stdin).get('response', '')[:80])")..."
else
    echo -e "${RED}❌${NC}"
    echo "   Error: $RESPONSE"
fi

# 4. List Models
echo -n "📦 List Models: "
RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/ollama/models \
  -b /tmp/pv_cookies.txt)
if echo "$RESPONSE" | grep -q '"models"'; then
    COUNT=$(echo "$RESPONSE" | python -c "import json,sys; print(len(json.load(sys.stdin).get('models', [])))")
    echo -e "${GREEN}✅${NC} ($COUNT models available)"
else
    echo -e "${RED}❌${NC}"
fi

# 5. Get Context
echo -n "📋 Get Context: "
RESPONSE=$(curl -s http://localhost:8000/api/v1/context/current \
  -b /tmp/pv_cookies.txt)
if echo "$RESPONSE" | grep -q '"context"'; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️${NC}"
fi

echo ""
echo -e "${GREEN}✅ API Test Complete!${NC}"
