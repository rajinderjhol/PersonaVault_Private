import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, make_response
from app.utils.auth import hash_password, verify_password, authenticate_user, error_response, session_required
from app.models.user import User
from app.models.user_session import UserSession as DbSession
from app.models.user_widget import UserWidget
from app.extensions import db
import json

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username, email, password = data.get('username'), data.get('email'), data.get('password')

        if not all([username, email, password]):
            return error_response("Missing required fields", 400)

        if db.session.query(User).filter((User.username == username) | (User.email == email)).first():
            return error_response("Username or email already exists", 409)

        new_user = User(username=username, email=email, password_hash=hash_password(password), role="user")
        db.session.add(new_user)
        db.session.flush()

        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + current_app.config['PERMANENT_SESSION_LIFETIME']
        db.session.add(DbSession(
            user_id=new_user.id, session_id=session_id, expires_at=expires_at
        ))
        db.session.commit()

        response = jsonify({"status": "success"})
        response.set_cookie('session_id', session_id, expires=expires_at, httponly=True, secure=current_app.config.get('SESSION_COOKIE_SECURE', False), samesite='Lax', path='/')
        return response
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return error_response("Registration failed", 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username, password = data.get('username'), data.get('password')
        if not all([username, password]): return error_response("Username and password required", 400)

        user = db.session.query(User).filter_by(username=username).first()
        if not user or not verify_password(password, user.password_hash):
            return error_response("Invalid credentials", 401)

        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + current_app.config['PERMANENT_SESSION_LIFETIME']
        db.session.add(DbSession(user_id=user.id, session_id=session_id, expires_at=expires_at))
        db.session.commit()

        response = jsonify({"status": "success"})
        response.set_cookie('session_id', session_id, expires=expires_at, httponly=True, secure=current_app.config.get('SESSION_COOKIE_SECURE', False), samesite='Lax', path='/')
        return response
    except Exception as e:
        logger.error(f"Login error: {e}")
        return error_response("Login failed", 500)

@auth_bp.route('/logout', methods=['POST'])
@session_required
def logout(user_id):
    try:
        session_id = request.cookies.get('session_id')
        db.session.query(DbSession).filter_by(session_id=session_id).delete()
        db.session.commit()
        response = jsonify({"status": "success"})
        response.delete_cookie('session_id', path='/')
        return response
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return error_response("Logout failed", 500)

@auth_bp.route('/validate-session', methods=['POST'])
def validate_session():
    try:
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"isAuthenticated": False, "theme": "light", "widgets": []}), 200

        user_id = authenticate_user(session_id)
        if not user_id: return jsonify({"isAuthenticated": False}), 401

        user = db.session.get(User, user_id)
        widget_data = db.session.query(UserWidget).filter_by(user_id=user_id).first()
        widgets = json.loads(widget_data.widgets) if widget_data else ["chat", "settings", "agent"]

        return jsonify({
            "isAuthenticated": True,
            "theme": user.theme if user else "light",
            "widgets": widgets
        }), 200
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return jsonify({"error": "Session validation failed"}), 500