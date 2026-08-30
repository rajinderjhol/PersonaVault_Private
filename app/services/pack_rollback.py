"""
Pack Rollback Service - Manage pack version rollbacks
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.models.pack_version import PackVersion, PackRollback
from app.services.pack_sandbox import PackSandbox
from runtime.pack_executor import PackExecutor

logger = logging.getLogger(__name__)


class PackRollbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sandbox = PackSandbox()
        self.executor = PackExecutor()

    async def list_versions(self, pack_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List all versions of a pack."""
        result = await self.db.execute(
            select(PackVersion)
            .where(PackVersion.pack_id == pack_id)
            .order_by(desc(PackVersion.created_at))
            .limit(limit)
        )
        versions = result.scalars().all()
        return [v.to_dict() for v in versions]

    async def get_version(self, pack_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Get a specific version of a pack."""
        result = await self.db.execute(
            select(PackVersion)
            .where(PackVersion.pack_id == pack_id)
            .where(PackVersion.version == version)
        )
        pack_version = result.scalar_one_or_none()
        return pack_version.to_dict() if pack_version else None

    async def create_version(self, pack_id: str, content: Dict[str, Any], 
                            changelog: str = None, author: str = None) -> Dict[str, Any]:
        """Create a new version of a pack."""
        # Get current active version
        current = await self.get_active_version(pack_id)
        
        # Parse version number
        version_parts = self._increment_version(current.version if current else "0.0.0")
        
        # Create new version
        pack_version = PackVersion(
            pack_id=pack_id,
            domain=content.get("domain", "unknown"),
            name=content.get("name", pack_id),
            version=version_parts,
            previous_version=current.version if current else None,
            pack_content=content,
            changelog=changelog,
            author=author,
            is_active=False
        )
        
        self.db.add(pack_version)
        await self.db.commit()
        await self.db.refresh(pack_version)
        
        return pack_version.to_dict()

    async def activate_version(self, pack_id: str, version: str) -> Dict[str, Any]:
        """Activate a specific version of a pack."""
        # Get the target version
        result = await self.db.execute(
            select(PackVersion)
            .where(PackVersion.pack_id == pack_id)
            .where(PackVersion.version == version)
        )
        target = result.scalar_one_or_none()
        if not target:
            raise ValueError(f"Version {version} not found for pack {pack_id}")
        
        # Deactivate all other versions
        await self.db.execute(
            select(PackVersion)
            .where(PackVersion.pack_id == pack_id)
            .where(PackVersion.is_active == True)
        )
        # Update active flag
        for v in await self.db.scalars(
            select(PackVersion).where(PackVersion.pack_id == pack_id)
        ):
            v.is_active = False
        
        target.is_active = True
        target.activated_at = datetime.utcnow()
        
        # Reload the pack in the executor
        await self.executor.reload_pack(pack_id, target.pack_content)
        
        await self.db.commit()
        await self.db.refresh(target)
        
        return target.to_dict()

    async def rollback(self, pack_id: str, target_version: str, 
                      reason: str = None, triggered_by: str = None) -> Dict[str, Any]:
        """Rollback a pack to a previous version."""
        # Get current active version
        current = await self.get_active_version(pack_id)
        if not current:
            raise ValueError(f"No active version found for pack {pack_id}")
        
        # Get target version
        result = await self.db.execute(
            select(PackVersion)
            .where(PackVersion.pack_id == pack_id)
            .where(PackVersion.version == target_version)
        )
        target = result.scalar_one_or_none()
        if not target:
            raise ValueError(f"Version {target_version} not found for pack {pack_id}")
        
        # Create rollback record
        rollback = PackRollback(
            pack_id=pack_id,
            from_version=current.version,
            to_version=target_version,
            reason=reason,
            triggered_by=triggered_by
        )
        self.db.add(rollback)
        
        # Activate target version
        await self.activate_version(pack_id, target_version)
        
        # Log the rollback
        logger.info(f"Rollback: {pack_id} from {current.version} to {target_version}")
        
        return {
            "status": "success",
            "message": f"Rolled back {pack_id} from {current.version} to {target_version}",
            "rollback": rollback.to_dict()
        }

    async def get_active_version(self, pack_id: str) -> Optional[PackVersion]:
        """Get the currently active version of a pack."""
        result = await self.db.execute(
            select(PackVersion)
            .where(PackVersion.pack_id == pack_id)
            .where(PackVersion.is_active == True)
        )
        return result.scalar_one_or_none()

    def _increment_version(self, version: str) -> str:
        """Increment semantic version (patch level)."""
        try:
            parts = version.split('.')
            if len(parts) >= 3:
                parts[2] = str(int(parts[2]) + 1)
                return '.'.join(parts)
            return f"{version}.1"
        except:
            return "1.0.0"
