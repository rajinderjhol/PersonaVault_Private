from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from app.core.permissions import ROLE_PERMISSIONS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from app.db.session import get_db
from app.models import User, UserSession
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

async def get_current_user_id(request: Request, db: AsyncSession = Depends(get_db)):
    """Validates the session cookie against the database."""
    session_token = request.cookies.get("session_id")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Use joinedload to fetch the User along with the Session to prevent N+1 later
    stmt = (
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.session_token == session_token)
        .where(UserSession.is_active == True)
        .where(UserSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None))
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
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Development login endpoint to authenticate the preseeded admin.
    """
    stmt = select(User).where(User.username == payload.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    # Verify the hashed password using bcrypt
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Create actual session record in database
    session_token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Session valid for 30 days if "stay signed in", else 24 hours
    expires_at = now + timedelta(days=30 if payload.stay_signed_in else 1)
    
    new_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        created_at=now,
        expires_at=expires_at,
        is_active=True
    )
    db.add(new_session)
    await db.commit()

    # IMPORTANT: Refresh the user instance to ensure its attributes are loaded. 
    # After a commit, SQLAlchemy expires all instances in the session. 
    # Refreshing prevents the MissingGreenlet error when attributes are accessed later.
    await db.refresh(user)

    # Set the cookie with the generated token
    max_age = 60 * 60 * 24 * 30 if payload.stay_signed_in else None
    response.set_cookie(
        key="session_id", 
        value=session_token, 
        httponly=True, 
        max_age=max_age,
        samesite="lax",
        path="/"
    )
    return {
        "status": "success", 
        "user": {
            "id": user.id, 
            "username": user.username, 
            "role": user.role
        }
    }

@router.post("/logout")
async def logout(response: Response):
    """Development logout endpoint to clear the session cookie."""
    response.delete_cookie(key="session_id")
    return {"status": "success"}

async def create_user(db: AsyncSession, **user_data):
    """
    Logic for creating a new user, utilized by enterprise management services.
    In a complete implementation, this would handle password hashing (e.g., using passlib)
    and persist the user to the database.
    """
    # Placeholder implementation to satisfy imports in enterprise.py
    return {"status": "created", "user_email": user_data.get("email"), "id": 1}