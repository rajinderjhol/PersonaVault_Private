"""
User Preferences API - Sidebar customization and user settings
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/user/preferences", tags=["user"])

# --- Sidebar Preferences ---

@router.get("/sidebar")
async def get_sidebar_prefs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's sidebar preferences."""
    # Return default preferences if not set
    prefs = current_user.sidebar_prefs if hasattr(current_user, 'sidebar_prefs') else None
    if not prefs:
        prefs = {
            "elements": [
                {"id": "dashboard", "type": "navigation", "label": "Dashboard", "icon": "📊", "visible": True},
                {"id": "chat", "type": "navigation", "label": "Chat", "icon": "💬", "visible": True},
                {"id": "swarm", "type": "navigation", "label": "Swarm", "icon": "🐝", "visible": True}
            ],
            "order": ["dashboard", "chat", "swarm"],
            "collapsed": False
        }
    return prefs

@router.post("/sidebar")
async def update_sidebar_prefs(
    prefs: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's sidebar preferences."""
    user = await db.merge(current_user)
    user.sidebar_prefs = prefs
    await db.commit()
    await db.refresh(user)
    return {"status": "updated", "prefs": prefs}

@router.post("/sidebar/elements")
async def add_sidebar_element(
    element: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new element to sidebar."""
    user = await db.merge(current_user)
    prefs = user.sidebar_prefs or {"elements": [], "order": []}
    
    # Check if element already exists
    existing = next((e for e in prefs["elements"] if e.get("id") == element.get("id")), None)
    if existing:
        return {"status": "exists", "element": element}
    
    # Add new element
    prefs["elements"].append(element)
    if element.get("id") not in prefs["order"]:
        prefs["order"].append(element["id"])
    
    user.sidebar_prefs = prefs
    await db.commit()
    await db.refresh(user)
    return {"status": "added", "element": element}

@router.delete("/sidebar/elements/{element_id}")
async def remove_sidebar_element(
    element_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove an element from sidebar."""
    user = await db.merge(current_user)
    prefs = user.sidebar_prefs or {"elements": [], "order": []}
    
    # Remove element
    prefs["elements"] = [e for e in prefs["elements"] if e.get("id") != element_id]
    prefs["order"] = [o for o in prefs["order"] if o != element_id]
    
    user.sidebar_prefs = prefs
    await db.commit()
    await db.refresh(user)
    return {"status": "removed", "element_id": element_id}

@router.post("/sidebar/order")
async def update_sidebar_order(
    order: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update sidebar element order."""
    user = await db.merge(current_user)
    prefs = user.sidebar_prefs or {"elements": [], "order": []}
    prefs["order"] = order
    user.sidebar_prefs = prefs
    await db.commit()
    await db.refresh(user)
    return {"status": "updated", "order": order}
