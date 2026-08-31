#!/bin/bash
set -e

# Assuming Alembic is used for migrations
echo "Applying database migrations..."
alembic upgrade head