from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import User, UserSession
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Validates session and returns the User object."""
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    stmt = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    
    user_stmt = select(User).where(User.id == session.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def get_current_user_id(request: Request, db: AsyncSession = Depends(get_db)) -> int:
    """Get the current user ID from the session."""
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    stmt = select(UserSession).where(
        UserSession.session_token == session_token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return session.user_id

class LoginRequest(BaseModel):
    username: str
    password: str
    stay_signed_in: bool = False

@router.post("/login")
async def login(payload: LoginRequest, response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == payload.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    session_token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(days=30 if payload.stay_signed_in else 1)
    
    new_session = UserSession(user_id=user.id, session_token=session_token, created_at=now, expires_at=expires_at, is_active=True)
    db.add(new_session)
    await db.commit()
    await db.refresh(user)

    max_age = 60 * 60 * 24 * 30 if payload.stay_signed_in else None
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        secure=False,  # Set to False to allow session cookies over HTTP in development
        max_age=max_age,
        samesite="lax",
        path="/",
    )
    
    return {"status": "success", "user": {"id": user.id, "username": user.username, "role": user.role}}

@router.post("/logout")
async def logout(response: Response, request: Request):
    response.delete_cookie(key="session_id", path="/")
    return {"status": "success"}

async def create_user(db: AsyncSession, **user_data):
    username = user_data.get("username")
    email = user_data.get("email")
    password = user_data.get("password")
    role = user_data.get("role", "user")
    organization_id = user_data.get("organization_id")
    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password, role=role, organization_id=organization_id)
    db.add(new_user)
    await db.flush()
    return {"status": "created", "user_email": email, "id": new_user.id}
