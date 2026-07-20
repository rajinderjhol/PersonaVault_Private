import functools
from flask import request, jsonify, current_app

def hash_password(password):
    # Replace with real PBKDF2 logic later
    return "hashed_" + password

def verify_password(password, hashed):
    return hashed == "hashed_" + password

def authenticate_user(session_id):
    return 1 # Returns a dummy user ID for development

def error_response(msg, code):
    return jsonify({"error": msg}), code

def session_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id')
        if not session_id:
            return error_response("Unauthorized: No session ID provided", 401)
        
        user_id = authenticate_user(session_id)
        if not user_id:
            return error_response("Unauthorized: Invalid or expired session", 401)
        
        return f(user_id, *args, **kwargs)
    return decorated