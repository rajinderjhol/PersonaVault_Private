"""
Behaviour Pack Loader for installing and validating packs.
"""
import logging
import yaml
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import BehaviourPack

logger = logging.getLogger(__name__)

class PackLoader:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def load_data_from_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Load pack data from YAML content."""
        data = yaml.safe_load(yaml_content)
        return data.get('pack', {}), data.get('policies', [])

    async def install_pack(self, yaml_content: str, user_id: int) -> bool:
        """Install a pack in the system."""
        pack_data, policies = self.load_data_from_yaml(yaml_content)
        
        db = self.session_factory()
        
        try:
            if isinstance(db, AsyncSession):
                return await self._run_install_pack(db, pack_data, policies, user_id)
            else:
                async with db as session:
                    return await self._run_install_pack(session, pack_data, policies, user_id)
        except Exception as e:
            logger.error(f"Failed to install pack: {e}")
            return False

    async def _run_install_pack(self, db: AsyncSession, pack_data: Dict[str, Any], policies: list, user_id: int) -> bool:
        try:
            stmt = select(BehaviourPack).where(BehaviourPack.id == pack_data.get('id'))
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                # Update fields
                existing.name = pack_data.get('name')
                existing.domain = pack_data.get('domain', 'general')
                existing.version = pack_data.get('version', '1.0.0')
                existing.description = pack_data.get('description', '')
                existing.policies = policies
                existing.is_active = pack_data.get('active', True)
                logger.info(f"✅ Pack {existing.name} updated successfully")
            else:
                new_pack = BehaviourPack(
                    id=pack_data.get('id'),
                    name=pack_data.get('name'),
                    domain=pack_data.get('domain', 'general'),
                    version=pack_data.get('version', '1.0.0'),
                    description=pack_data.get('description', ''),
                    policies=policies,
                    temporal_patterns=pack_data.get('temporal_patterns', []),
                    is_active=pack_data.get('active', True),
                    installed_at=datetime.utcnow(),
                    installed_by=user_id
                )
                db.add(new_pack)
                logger.info(f"✅ Pack {new_pack.name} installed successfully")
            
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to install pack: {e}")
            await db.rollback()
            return False

    async def list_installed_packs(self) -> list:
        """Return all installed packs."""
        db = self.session_factory()
        if isinstance(db, AsyncSession):
            stmt = select(BehaviourPack)
            result = await db.execute(stmt)
            return result.scalars().all()
        else:
            async with db as session:
                stmt = select(BehaviourPack)
                result = await session.execute(stmt)
                return result.scalars().all()
