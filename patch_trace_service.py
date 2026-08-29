import re

# Read the current file
with open('app/services/trace_service.py', 'r') as f:
    content = f.read()

# Add selectinload import if missing
if 'from sqlalchemy.orm import selectinload' not in content:
    content = content.replace(
        'from sqlalchemy.future import select',
        'from sqlalchemy.future import select\nfrom sqlalchemy.orm import selectinload'
    )

# Update get_full_trace with eager loading
content = re.sub(
    r'(async def get_full_trace.*?)(select\(DecisionTrace\)\.filter\(DecisionTrace\.id == trace_id\))',
    r'\1select(DecisionTrace).options(selectinload(DecisionTrace.provenance_links)).filter(DecisionTrace.id == trace_id)',
    content,
    flags=re.DOTALL
)

# Update get_session_traces with eager loading
content = re.sub(
    r'(async def get_session_traces.*?)(select\(DecisionTrace\)\s*\.filter\(DecisionTrace\.session_id == session_id\))',
    r'\1select(DecisionTrace).options(selectinload(DecisionTrace.provenance_links)).filter(DecisionTrace.session_id == session_id)',
    content,
    flags=re.DOTALL
)

# Update get_recent_traces with eager loading
content = re.sub(
    r'(async def get_recent_traces.*?)(select\(DecisionTrace\)\s*\.order_by\(DecisionTrace\.timestamp\.desc\(\)\)\.limit\(limit\))',
    r'\1select(DecisionTrace).options(selectinload(DecisionTrace.provenance_links)).order_by(DecisionTrace.timestamp.desc()).limit(limit)',
    content,
    flags=re.DOTALL
)

with open('app/services/trace_service.py', 'w') as f:
    f.write(content)
print("✅ Updated trace service with eager loading")
