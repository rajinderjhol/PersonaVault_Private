import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.models.marketplace import (
    MarketplacePack, PackMetadata, PackStatistics, 
    PackVersion, PackStatus, PackCategory
)

logger = logging.getLogger(__name__)


class PackManager:
    """Manages pack installation, removal, and updates."""
    
    def __init__(self, packs_dir: Optional[Path] = None):
        self.packs_dir = packs_dir or Path("app/packs")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pack_install_"))
        self.installed_packs = {}
        self._load_installed_packs()
    
    def _load_installed_packs(self):
        """Load all installed packs from disk."""
        if not self.packs_dir.exists():
            return
        
        for pack_path in self.packs_dir.glob("*/pack.yaml"):
            try:
                import yaml
                with open(pack_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                pack_id = config.get("pack", {}).get("name")
                if pack_id:
                    self.installed_packs[pack_id] = {
                        "path": str(pack_path.parent),
                        "config": config,
                        "version": config.get("pack", {}).get("version", "1.0.0")
                    }
            except Exception as e:
                logger.error(f"Failed to load pack {pack_path}: {e}")
        
        logger.info(f"Loaded {len(self.installed_packs)} installed packs")
    
    async def install_pack(
        self, 
        pack_data: bytes, 
        pack_id: str,
        version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """Install a pack from uploaded data."""
        try:
            # Create temp file
            temp_path = self.temp_dir / f"{pack_id}_{version}.tar.gz"
            with open(temp_path, 'wb') as f:
                f.write(pack_data)
            
            # Extract pack
            import tarfile
            extract_path = self.packs_dir / pack_id
            extract_path.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall(extract_path)
            
            # Validate pack
            pack_config = await self._validate_pack(extract_path)
            
            # Load pack
            self.installed_packs[pack_id] = {
                "path": str(extract_path),
                "config": pack_config,
                "version": version
            }
            
            logger.info(f"Installed pack: {pack_id} v{version}")
            
            return {
                "success": True,
                "pack_id": pack_id,
                "version": version,
                "path": str(extract_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to install pack {pack_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def uninstall_pack(self, pack_id: str) -> Dict[str, Any]:
        """Uninstall a pack."""
        if pack_id not in self.installed_packs:
            return {
                "success": False,
                "error": f"Pack {pack_id} not installed"
            }
        
        try:
            import shutil
            pack_path = Path(self.installed_packs[pack_id]["path"])
            shutil.rmtree(pack_path)
            
            del self.installed_packs[pack_id]
            
            logger.info(f"Uninstalled pack: {pack_id}")
            
            return {
                "success": True,
                "pack_id": pack_id
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall pack {pack_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_pack(self, pack_path: Path) -> Dict[str, Any]:
        """Validate a pack installation."""
        import yaml
        
        config_path = pack_path / "pack.yaml"
        if not config_path.exists():
            raise ValueError(f"pack.yaml not found in {pack_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required fields
        pack_data = config.get("pack", {})
        required_fields = ["name", "version", "domain"]
        for field in required_fields:
            if field not in pack_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate directories
        for dir_name in ["policies", "agents", "crystallized"]:
            if not (pack_path / dir_name).exists():
                logger.warning(f"Missing directory: {dir_name}")
        
        return config
    
    def get_installed_packs(self) -> List[Dict[str, Any]]:
        """Get list of installed packs."""
        return [
            {
                "id": pack_id,
                "name": data["config"].get("pack", {}).get("name", pack_id),
                "version": data["version"],
                "domain": data["config"].get("pack", {}).get("domain", "unknown"),
                "path": data["path"]
            }
            for pack_id, data in self.installed_packs.items()
        ]
