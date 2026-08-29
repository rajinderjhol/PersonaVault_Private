#!/bin/bash
echo "🔐 Logging in..."
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c cookies.txt

echo -e "\n📊 Testing phase distribution..."
curl -s http://localhost:8000/api/v1/thermodynamics/phase-distribution -b cookies.txt | python -m json.tool

echo -e "\n💬 Testing chat sessions..."
curl -s http://localhost:8000/api/v1/chat/sessions -b cookies.txt | python -m json.tool

echo -e "\n🔍 Testing decision traces..."
curl -s http://localhost:8000/api/v1/traces/recent -b cookies.txt | python -m json.tool
