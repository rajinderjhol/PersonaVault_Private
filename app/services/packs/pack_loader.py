"""
Behaviour Pack Loader for installing and validating packs.
"""
import logging
import yaml
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.learning.behaviour_pack import BehaviourPack

logger = logging.getLogger(__name__)

class PackLoader:
    """Load and validate Behaviour Packs."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def load_pack_from_yaml(self, yaml_content: str, user) -> Optional[BehaviourPack]:
        """Load a pack from YAML content."""
        try:
            data = yaml.safe_load(yaml_content)
            
            if not data:
                logger.error("Empty YAML content")
                return None
                
            if "pack" not in data:
                logger.error("Invalid pack: missing 'pack' section")
                return None
            
            pack_data = data["pack"]
            
            # Extract user ID - handle both User object and integer
            if hasattr(user, 'id'):
                user_id = user.id
            else:
                user_id = int(user)
            
            logger.info(f"📝 Installing pack for user_id: {user_id}")
            
            # Create pack object
            pack = BehaviourPack(
                id=pack_data.get("id", f"pack-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                name=pack_data.get("name", "Unnamed Pack"),
                version=pack_data.get("version", "1.0.0"),
                domain=pack_data.get("domain", "general"),
                description=pack_data.get("description", ""),
                entities=pack_data.get("entities", []),
                events=pack_data.get("events", []),
                decision_types=pack_data.get("decision_types", []),
                metrics=pack_data.get("metrics", []),
                prompts=pack_data.get("prompts", {}),
                views=pack_data.get("views", {}),
                policies=pack_data.get("policies", []),
                evaluation_rules=pack_data.get("evaluation_rules", []),
                installed_by=user_id
            )
            
            logger.info(f"✅ Pack loaded: {pack.name} (ID: {pack.id}, installed_by: {pack.installed_by})")
            return pack
            
        except Exception as e:
            logger.error(f"Error loading pack: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def install_pack(self, pack: BehaviourPack) -> bool:
        """Install a pack in the system."""
        async with self.session_factory() as db:
            try:
                # Check if pack already exists
                from sqlalchemy import select
                stmt = select(BehaviourPack).where(BehaviourPack.id == pack.id)
                result = await db.execute(stmt)
                existing = result.scalars().first()
                
                if existing:
                    logger.warning(f"Pack {pack.id} already exists, updating...")
                    # Update existing pack
                    for key, value in pack.__dict__.items():
                        if not key.startswith('_') and key != 'installed_at':
                            setattr(existing, key, value)
                else:
                    db.add(pack)
                
                await db.commit()
                logger.info(f"✅ Pack {pack.name} installed successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to install pack: {e}")
                import traceback
                logger.error(traceback.format_exc())
                await db.rollback()
                return False
    
    async def get_pack(self, pack_id: str) -> Optional[BehaviourPack]:
        """Get a pack by ID."""
        async with self.session_factory() as db:
            from sqlalchemy import select
            stmt = select(BehaviourPack).where(BehaviourPack.id == pack_id)
            result = await db.execute(stmt)
            return result.scalars().first()
    
    async def list_packs(self) -> list:
        """List all installed packs."""
        async with self.session_factory() as db:
            from sqlalchemy import select
            stmt = select(BehaviourPack).where(BehaviourPack.is_active == True)
            result = await db.execute(stmt)
            return result.scalars().all()
