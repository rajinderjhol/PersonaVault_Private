#!/usr/bin/env bash
set -euo pipefail

BACKEND="http://localhost:8000"
DOCS="/home/rajinderj8888/personavault/test_docs/contracts"
CONTAINER="personavault-postgres"
COOKIES=/tmp/demo-cookies.txt

# Helper to run psql
psql_exec() {
    docker exec -i $CONTAINER psql -U personavault -d personavault -t -c "$1"
}

# 0. Login
curl -s -c "$COOKIES" -X POST "$BACKEND/api/v1/auth/login"   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=admin&password=admin123" > /dev/null

if grep -q "session_id" "$COOKIES"; then
    echo "✓ Logged in as admin"
else
    echo "⚠ Login failed."
    exit 1
fi

# 1. Pre-state
echo "=== 0. Pre-state ==="
psql_exec "SELECT count(*) FROM semantic_patterns;"

# 2. Ingest
echo "=== 1. Ingest ==="
INGEST_RESP=$(curl -s -b "$COOKIES" -X POST "$BACKEND/api/v1/ingestion/folder"   -H "Content-Type: application/json"   -d "{\"folder_path\": \"$DOCS\", \"user_id\": 1, \"recursive\": true}")
JOB_ID=$(echo "$INGEST_RESP" | jq -r '.job_id // empty')

if [ -z "$JOB_ID" ]; then
    echo "⚠ Ingest request failed: $INGEST_RESP"
    exit 1
fi
echo "Job initiated: $JOB_ID"

MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    RESP=$(curl -s -b "$COOKIES" "$BACKEND/api/v1/ingestion/job/$JOB_ID")
    STATUS=$(echo "$RESP" | jq -r '.status // "unknown"')
    echo "Status: $STATUS ($WAITED s)"
    [ "$STATUS" == "completed" ] && break
    if [ "$STATUS" == "failed" ]; then
        echo "Job failed: $RESP"
        exit 1
    fi
    sleep 5
    WAITED=$((WAITED + 5))
done
[ $WAITED -ge $MAX_WAIT ] && echo "⚠ Timeout" && exit 1

# 3. Checkpoint: Patterns
echo "=== 2. Checkpoint: Patterns ==="
psql_exec "SELECT pattern_type, count(*) FROM semantic_patterns GROUP BY pattern_type;"
psql_exec "SELECT min(weight), avg(weight), max(weight) FROM semantic_patterns;"

# 4. Retrieve
echo "=== 3. Retrieve ==="
PATTERNS_RESP=$(curl -s -b "$COOKIES" "$BACKEND/api/v1/patterns/?limit=3")
PATTERN_COUNT=$(echo "$PATTERNS_RESP" | jq -r '.patterns | length')
echo "Patterns retrieved: $PATTERN_COUNT"

# 5. Detail
echo "=== 4. Pattern detail ==="
PATTERN_ID=$(echo "$PATTERNS_RESP" | jq -r '.patterns[0].id // empty')
if [ -n "$PATTERN_ID" ]; then
  echo "Found pattern: $PATTERN_ID"
  curl -s -b "$COOKIES" "$BACKEND/api/v1/patterns/$PATTERN_ID" | jq '{trigger, pattern_type, weight}'
else
  echo "No patterns to retrieve"
fi
