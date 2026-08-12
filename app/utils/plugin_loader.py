import json
import os
import logging
from typing import List, Dict, Any
from app.utils.sandboxed_runner import SandboxedPluginRunner

logger = logging.getLogger(__name__)

class PluginLoader:
    @staticmethod
    def load_plugins(plugins_dir: str = "plugins") -> List[Dict[str, Any]]:
        """Scans plugins directory for plugin_manifest.json and loads them in a sandbox."""
        loaded_plugins = []
        
        # Ensure plugins directory exists
        if not os.path.exists(plugins_dir):
            logger.warning(f"Plugins directory {plugins_dir} not found.")
            return []
            
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            if not os.path.isdir(plugin_path):
                continue
            
            manifest_path = os.path.join(plugin_path, "plugin_manifest.json")
            if not os.path.exists(manifest_path):
                continue
                
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                if not manifest.get("enabled", True):
                    continue
                    
                # Wrap the handler in a SandboxedPluginRunner
                runner = SandboxedPluginRunner(manifest["handler_module"], manifest["handler_function"])
                
                loaded_plugins.append({
                    "name": manifest["name"],
                    "description": manifest["description"],
                    "parameters": manifest.get("parameters", {}),
                    "handler": runner.run
                })
                logger.info(f"✅ Loaded sandboxed plugin: {manifest['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to load plugin {plugin_name}: {e}")
                
        return loaded_plugins
