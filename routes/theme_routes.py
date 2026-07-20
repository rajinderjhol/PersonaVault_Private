import logging
from flask import Blueprint, request, jsonify
from app.utils.auth import session_required
from app.extensions import db
from app.models.user import User

theme_bp = Blueprint('theme', __name__)
logger = logging.getLogger(__name__)

DEFAULT_THEME = 'light'

@theme_bp.route('/get-theme', methods=['GET'])
@session_required
def get_theme(user_id):
    """Retrieve user's theme preference."""
    try:
        user = User.query.get(user_id)
        return jsonify({"theme": user.theme if user else DEFAULT_THEME})
    except Exception as e:
        logger.error(f"Theme fetch error: {e}")
        return jsonify({"error": "Failed to retrieve theme"}), 500

@theme_bp.route('/save-theme', methods=['POST'])
@session_required
def save_theme(user_id):
    """Update user's theme preference."""
    try:
        data = request.json
        theme = data.get('theme', DEFAULT_THEME)
        
        user = User.query.get(user_id)
        if user:
            user.theme = theme
            db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Theme save error: {e}")
        return jsonify({"error": "Failed to save theme"}), 500