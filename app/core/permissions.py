# RBAC Permission Definitions

ROLE_PERMISSIONS = {
    "admin": ["*"],  # All access
    "org_manager": ["read:org", "write:org", "read:user"],
    "user": ["read:user", "read:memory", "write:memory", "database_query", "file_search", "web_search", "ai_generate", "memory_search"],
    "auditor": ["read:audit"]
}

# Mapping tools to required permissions
TOOL_PERMISSIONS = {
    "database_query": "read:memory",
    "email_search": "read:memory",
    "file_search": "read:memory",
    "web_search": "read:memory",
    "ai_generate": "write:memory",
    "memory_search": "read:memory",
    "pattern_explore": "read:audit"
}

# Mapping path prefixes to required permissions
PATH_PERMISSIONS = {
    "/api/v1/admin": "admin",
    "/api/v1/organizations": "write:org",
    "/api/v1/memory": "read:memory",
    "/api/v1/audit": "read:audit",
}

def check_permission(user_role: str, path: str, org_id: int = None) -> bool:
    if user_role == "admin":
        return True
        
    required_perm = None
    for prefix, perm in PATH_PERMISSIONS.items():
        if path.startswith(prefix):
            required_perm = perm
            break
            
    if not required_perm:
        return True # Default allow for unknown paths
    
    # Future-proofing: add logic to check org_id against user's organization
    return required_perm in ROLE_PERMISSIONS.get(user_role, [])

def check_tool_permission(user_role: str, tool_name: str) -> bool:
    if user_role == "admin":
        return True
    
    required_perm = TOOL_PERMISSIONS.get(tool_name)
    if not required_perm:
        return True # Default allow for unregistered tools
        
    return required_perm in ROLE_PERMISSIONS.get(user_role, [])
