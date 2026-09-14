
import pytest
from sqlalchemy import inspect
from app.db.session import Base

async def run_consistency_check(engine) -> list[str]:
    """Returns a list of mismatch strings. Empty list means consistent."""
    mismatches = []
    async with engine.connect() as conn:
        def _check(sync_conn):
            insp = inspect(sync_conn)
            for table_name, table in Base.metadata.tables.items():
                if not insp.has_table(table_name):
                    continue
                db_cols = {c["name"] for c in insp.get_columns(table_name)}
                model_cols = {c.name for c in table.columns}
                if db_cols != model_cols:
                    mismatches.append(
                        f"{table_name}: model_only={model_cols - db_cols} "
                        f"db_only={db_cols - model_cols}"
                    )
        await conn.run_sync(_check)
    return mismatches
