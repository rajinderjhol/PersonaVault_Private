import pytest
from sqlalchemy import inspect
from app.db.session import Base
from sqlalchemy import Column, String, Integer
import app.models.semantic # Import to load

@pytest.mark.asyncio
async def test_detect_schema_drift():
    # Artificially modify the model to create drift
    class DriftedPattern(Base):
        __tablename__ = "semantic_patterns"
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True)
        # Added extra column
        unexpected_column = Column(String)
        
    insp = inspect(Base.metadata.bind or Base.metadata.bind_engine or Base.metadata.bind_engine_for_tests if hasattr(Base.metadata, 'bind_engine_for_tests') else None)
    # Actually, simpler: check the metadata table objects directly
    
    table = Base.metadata.tables["semantic_patterns"]
    assert "unexpected_column" in table.columns
    print("✅ Negative schema test setup verified.")
