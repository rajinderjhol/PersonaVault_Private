#!/usr/bin/env bash
CONTAINER="personavault-postgres"
docker exec -i $CONTAINER psql -U personavault -d personavault -c "
TRUNCATE semantic_patterns, behaviour_events RESTART IDENTITY CASCADE;
"
echo "✓ Demo state reset"
