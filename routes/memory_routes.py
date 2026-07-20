import logging
from flask import Blueprint, request, jsonify
from app.utils.auth import session_required
from app.extensions import db
from app.models.memory import Memory
from app.services.memory_service import MemoryService

memory_bp = Blueprint('memory', __name__)
logger = logging.getLogger(__name__)

@memory_bp.route('/memories', methods=['GET'])
@session_required
def get_memories(user_id):
    """Endpoint to fetch memories for the logged-in user."""
    try:
        memories = Memory.query.filter_by(user_id=user_id).all()
        return jsonify({
            "memories": [{
                "id": m.id,
                "title": m.title,
                "content": m.content,
                "tags": m.tags,
                "created_at": m.created_at.isoformat()
            } for m in memories]
        })
    except Exception as e:
        logger.error(f"Memory fetch error: {e}")
        return jsonify({"error": "Failed to retrieve memories"}), 500

@memory_bp.route('/memories', methods=['POST'])
@session_required
def save_memory(user_id):
    """Endpoint to save a new memory."""
    try:
        data = request.json
        if not data or 'content' not in data or 'title' not in data:
            return jsonify({"error": "Missing title or content"}), 400

        service = MemoryService(db.session)
        new_memory = service.save_memory(
            user_id=user_id,
            memory_type=data.get('memory_type', 'note'),
            content=data['content'],
            tags=data.get('tags', [])
        )
        return jsonify({"status": "success", "id": new_memory.id}), 201
    except Exception as e:
        logger.error(f"Save memory error: {e}")
        return jsonify({"error": "Failed to save memory"}), 500