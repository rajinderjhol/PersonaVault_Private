import logging
from flask import Blueprint, request, jsonify
from app.utils.auth import session_required
from app.extensions import db
from app.models.ai_setting import AISetting
from app.services.vault import vault

settings_bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@settings_bp.route('/ai-settings', methods=['GET', 'POST'])
@session_required
def handle_ai_settings(user_id):
    """Manage AI configuration profiles."""
    if request.method == 'GET':
        try:
            settings = AISetting.query.filter_by(user_id=user_id).all()
            results = [{
                'id': s.id,
                'profile_name': s.profile_name,
                'provider_type': s.provider_type,
                'deployment_type': s.deployment_type,
                'model_name': s.model_name,
                'temperature': s.temperature,
                'max_tokens': s.max_tokens,
                'system_prompt': s.system_prompt
            } for s in settings]
            return jsonify(results)
        except Exception as e:
            logger.error(f"AI settings fetch error: {str(e)}")
            return jsonify({"error": "Failed to retrieve settings"}), 500

    elif request.method == 'POST':
        try:
            data = request.json.get('settings', {})
            required = ['profile_name', 'model_name', 'provider_type', 'deployment_type']
            if not all(data.get(k) for k in required):
                return jsonify({"error": "Missing required fields"}), 400
            
            encrypted_key = vault.encrypt(data.get('api_key', ''))
            
            new_setting = AISetting(
                user_id=user_id,
                profile_name=data['profile_name'],
                model_name=data['model_name'],
                provider_type=data['provider_type'],
                deployment_type=data['deployment_type'],
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 100),
                system_prompt=data.get('system_prompt', ''),
                api_key_enc=encrypted_key,
                api_endpoint=data.get('api_endpoint', '')
            )
            db.session.add(new_setting)
            db.session.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            logger.error(f"AI settings save error: {str(e)}")
            return jsonify({"error": "Failed to save configuration"}), 500

@settings_bp.route('/widget-config', methods=['GET'])
@session_required
def get_widget_config(user_id):
    """Return standardized widget configuration."""
    try:
        # Standard widget configuration (could be moved to Config class)
        widget_config = {
            "chat": {
                "endpoint": "/api/ollama/chat",
                "model": "default",
                "temperature": 0.7
            },
            "settings": {
                "theme": "light",
                "profile_name": "Default"
            },
            "agent": {
                "endpoint": "/agent",
                "model": "default"
            }
        }
        return jsonify(widget_config)
    except Exception as e:
        logger.error(f"Failed to fetch widget config: {e}")
        return jsonify({"error": "Failed to retrieve widget config"}), 500