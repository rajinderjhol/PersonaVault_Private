from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Use JSONB on Postgres, JSON on SQLite. Same model works on both.
JSONType = JSON().with_variant(JSONB, "postgresql")
