import re

with open('app/main.py', 'r') as f:
    content = f.read()

# Find and fix the chat_endpoint function
old = '''async def chat_endpoint(request: Request, current_user: User = Depends(get_current_user)):
    """
    Unified chat endpoint - uses the Intelligence Gateway.
    This is the main user-facing chat interface.
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        patient_id = data.get("patient_id")
        provider = data.get("provider", "ollama")
        session_id = data.get("session_id")
        
        if not query:
            return {"error": "Query is required"}
        
        # Get response
        result = await gateway.chat(current_user.id, query, request.app.state, patient_id=patient_id, provider=provider)'''

new = '''async def chat_endpoint(request: Request, current_user: User = Depends(get_current_user)):
    """
    Unified chat endpoint - uses the Intelligence Gateway.
    This is the main user-facing chat interface.
    """
    result = None
    try:
        data = await request.json()
        query = data.get("query", "")
        patient_id = data.get("patient_id")
        provider = data.get("provider", "ollama")
        session_id = data.get("session_id")
        
        if not query:
            return {"error": "Query is required"}
        
        # Get response
        result = await gateway.chat(current_user.id, query, request.app.state, patient_id=patient_id, provider=provider)'''

content = content.replace(old, new)

with open('app/main.py', 'w') as f:
    f.write(content)

print("✅ Fixed chat endpoint")
