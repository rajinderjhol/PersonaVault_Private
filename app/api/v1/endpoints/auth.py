from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import User, UserSession
import uuid
import os
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

    # Detect if we are in Cloud Shell or Development to set appropriate cookie flags
    is_dev = os.getenv("APP_ENV") == "development" or os.getenv("CLOUD_SHELL") == "true"
    max_age = 30 * 24 * 60 * 60 if payload.stay_signed_in else 24 * 60 * 60
    
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        secure=True if is_dev else False, # Secure must be True for SameSite=None
        max_age=max_age,
        samesite="none" if is_dev else "lax",
        path="/",
    )
    
    return {"status": "success", "user": {"id": user.id, "username": user.username, "role": user.role}}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role}

@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by invalidating the current session.
    """
    try:
        # Get session token from cookie
        session_token = request.cookies.get("session_id")
        
        if session_token:
            # Find and deactivate the session
            stmt = select(UserSession).where(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                session.is_active = False
                # Assuming ended_at column exists, if not, skip this
                if hasattr(session, 'ended_at'):
                    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await db.commit()
        
        # Clear the cookie
        response = JSONResponse(
            content={"status": "success", "message": "Logged out successfully"}
        )
        response.delete_cookie("session_id", path="/")
        return response
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

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
