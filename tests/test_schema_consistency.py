import pytest
from sqlalchemy import inspect
from app.db.session import Base, engine
from app.models.semantic import SemanticPattern  # Import one model to trigger loading

@pytest.mark.asyncio
async def test_all_models_match_db():
    async with engine.connect() as conn:
        def _check(sync_conn):
            insp = inspect(sync_conn)
            mismatches = []
            
            # Get table names from metadata
            # We filter for tables that actually exist in the DB
            tables = Base.metadata.tables
            
            for table_name, table in tables.items():
                if not insp.has_table(table_name):
                    continue
                    
                db_cols = {c["name"] for c in insp.get_columns(table_name)}
                model_cols = {c.name for c in table.columns}
                
                if db_cols != model_cols:
                    mismatches.append(
                        f"Table '{table_name}': "
                        f"model_only={model_cols - db_cols} "
                        f"db_only={db_cols - model_cols}"
                    )
            return mismatches
            
        mismatches = await conn.run_sync(_check)
    assert not mismatches, "Schema drift detected:\n" + "\n".join(mismatches)
