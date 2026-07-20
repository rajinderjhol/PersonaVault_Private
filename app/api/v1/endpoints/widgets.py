from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import json
from app.db.session import get_db
from app.models import UserWidget
from app.api.v1.endpoints.auth import get_current_user_id

router = APIRouter()

class WidgetLayout(BaseModel):
    widgets: list

@router.get("/config")
async def get_widget_config(user_id: int = Depends(get_current_user_id)):
    """Static or dynamic config for specific widget behaviors"""
    return {
        "chat": {"endpoint": "/api/ollama/chat", "model": "default"},
        "settings": {"profile_name": "Default"},
        "agent": {"endpoint": "/api/agent", "model": "default"}
    }

@router.get("/")
async def get_user_widgets(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    stmt = select(UserWidget).where(UserWidget.user_id == user_id)
    result = await db.execute(stmt)
    widget_entry = result.scalars().first()
    if not widget_entry:
        return ["chat", "settings", "agent"]
    return json.loads(widget_entry.widgets)

@router.post("/")
async def save_widget_layout(
    data: WidgetLayout, 
    user_id: int = Depends(get_current_user_id), 
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserWidget).where(UserWidget.user_id == user_id)
    result = await db.execute(stmt)
    widget_entry = result.scalars().first()
    
    widgets_json = json.dumps(data.widgets)
    
    if widget_entry:
        widget_entry.widgets = widgets_json
    else:
        new_entry = UserWidget(
            user_id=user_id,
            widgets=widgets_json
        )
        db.add(new_entry)
    
    await db.commit()
    return {"status": "success"}