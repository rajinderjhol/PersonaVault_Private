import asyncio
import json
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.decision_trace import DecisionTrace

async def populate_pack_names():
    async with SessionLocal() as db:
        result = await db.execute(select(DecisionTrace))
        traces = result.scalars().all()
        
        updated_count = 0
        for trace in traces:
            # Extract pack_name from data JSON if available
            if trace.data and isinstance(trace.data, dict):
                pack_name = trace.data.get("pack_name") or trace.data.get("domain")
                # Also try to extract from query if it contains keywords
                if not pack_name and trace.query:
                    query_lower = trace.query.lower()
                    if "security" in query_lower: pack_name = "security"
                    elif "compliance" in query_lower: pack_name = "compliance"
                    elif "contract" in query_lower: pack_name = "contract"
                    elif "procurement" in query_lower: pack_name = "procurement"
                
                if pack_name and not trace.pack_name:
                    trace.pack_name = pack_name
                    updated_count += 1
                    print(f"Updated trace {trace.id} with pack_name: {pack_name}")
        
        await db.commit()
        print(f"✅ Migration complete! Updated {updated_count} traces.")

asyncio.run(populate_pack_names())
