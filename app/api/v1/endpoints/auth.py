from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
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
    return await get_current_user_logic(request, db)

async def get_current_user_logic(request: Request, db: AsyncSession):
    """Core logic to validate session and return User object."""
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


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login | PersonaVault</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="/static/css/dashboard.css">
        <style>
            body {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: #020617;
            }
            .login-card {
                width: 100%;
                max-width: 400px;
                padding: 30px;
                text-align: center;
            }
            .login-header {
                margin-bottom: 25px;
            }
            .login-header h2 {
                color: var(--accent);
                font-size: 24px;
                margin: 10px 0 5px 0;
            }
            .login-header p {
                color: #94a3b8;
                font-size: 14px;
            }
            .form-group {
                text-align: left;
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 5px;
                font-weight: 600;
            }
            .input-field {
                width: 100%;
                margin: 0;
            }
            .btn-login {
                width: 100%;
                padding: 10px;
                font-size: 14px;
                margin-top: 10px;
            }
            .stay-signed-in {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 13px;
                color: #94a3b8;
                margin-top: 15px;
                cursor: pointer;
            }
            .stay-signed-in input {
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="card login-card">
            <div class="login-header">
                <i class="fas fa-shield-halved" style="font-size: 40px; color: var(--accent);"></i>
                <h2>PersonaVault</h2>
                <p>Secure Intelligence Gateway</p>
            </div>
            <form action="/api/v1/auth/login" method="post">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" class="input-field" placeholder="Enter your username" required autofocus>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" class="input-field" placeholder="Enter your password" required>
                </div>
                <label class="stay-signed-in">
                    <input type="checkbox" name="stay_signed_in" value="true">
                    Stay signed in for 30 days
                </label>
                <button type="submit" class="btn btn-login">
                    <i class="fas fa-sign-in-alt"></i> Login to System
                </button>
            </form>
            <div style="margin-top: 20px; font-size: 11px; color: #475569;">
                &copy; 2026 PersonaVault Sovereign Intelligence
            </div>
        </div>
    </body>
    </html>
    """)

@router.post("/login")
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
    stay_signed_in: bool = Form(False)
):
    logger.info(f"Login attempt for user: {username}")
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not pwd_context.verify(password, user.hashed_password):
        logger.warning(f"Invalid credentials for user: {username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    session_token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(days=30 if stay_signed_in else 1)
    
    new_session = UserSession(user_id=user.id, session_token=session_token, created_at=now, expires_at=expires_at, is_active=True)
    db.add(new_session)
    await db.commit()
    await db.refresh(user)
    logger.info(f"Session created for user: {user.id}")

    # Detect if we are in Cloud Shell or Development to set appropriate cookie flags
    is_cloud_shell = os.getenv("CLOUD_SHELL") == "true" or ".cloudshell.dev" in str(request.base_url)
    is_dev = os.getenv("APP_ENV") == "development"
    
    # We should use Secure=True if we're on HTTPS (including Cloud Shell proxy)
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https" or is_cloud_shell
    
    max_age = 30 * 24 * 60 * 60 if stay_signed_in else 24 * 60 * 60
    
    # After successful login, redirect to dashboard
    logger.info(f"Redirecting user {username} to dashboard. HTTPS={is_https}, CloudShell={is_cloud_shell}")
    response = RedirectResponse(url="/api/v1/admin/dashboard/", status_code=status.HTTP_303_SEE_OTHER)
    
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        secure=is_https,   # Secure if HTTPS
        max_age=max_age,
        samesite="lax",    # Lax is generally good for redirects
        path="/",
    )
    
    return response

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
