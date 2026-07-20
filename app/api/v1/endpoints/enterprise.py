from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
from app.db.session import get_db
from app.models import Organization, User, Role, APIKey, AuditLog
from app.core.dependencies import require_admin, require_org_manage, require_audit_read
from app.core.permissions import ROLE_PERMISSIONS
from app.api.v1.endpoints.auth import create_user

router = APIRouter(prefix="/enterprise", tags=["enterprise"])

@router.post("/organizations")
async def create_organization(
    name: str,
    slug: str,
    admin_email: str,
    admin_username: str,
    admin_password: str,
    db: AsyncSession = Depends(get_db)
):
    """Onboard a new organization with an admin user."""
    stmt = select(Organization).where(Organization.slug == slug)
    result = await db.execute(stmt)
    existing_org = result.scalars().first()
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization slug already exists")

    org = Organization(name=name, slug=slug, subscription_tier="pro")
    db.add(org)
    await db.flush()
    
    # Create initial admin user
    admin = await create_user(
        username=admin_username,
        email=admin_email,
        password=admin_password,
        role="admin",
        organization_id=org.id,
        db=db
    )
    
    # Initialize default roles for the organization
    for role_name, permissions in ROLE_PERMISSIONS.items():
        role = Role(organization_id=org.id, name=role_name, permissions=permissions)
        db.add(role)
    
    await db.commit()
    return {"organization_id": org.id, "admin_id": admin.get("id")}

@router.post("/api-keys")
async def create_api_key(
    name: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create an API key for a user."""
    key = "pv_" + secrets.token_urlsafe(32)
    api_key = APIKey(
        user_id=user_id,
        key=key,
        name=name,
        permissions=["memory:read", "memory:write"]
    )
    db.add(api_key)
    await db.commit()
    return {"api_key": key, "id": api_key.id}

@router.get("/audit")
async def get_audit_logs(
    user_id: int = Depends(require_audit_read),
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve organization audit trails."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    stmt = select(AuditLog).where(
        AuditLog.organization_id == user.organization_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs