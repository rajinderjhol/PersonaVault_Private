import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import json

from app.swarm.core.generator import GeneratorAgent

logger = logging.getLogger(__name__)

class DiscoveryService:
    """
    V3 Discovery Engine: Autonomously scans environments and suggests 
    PersonaVault Behaviour Packs.
    """
    
    def __init__(self, generator: Optional[GeneratorAgent] = None):
        self.generator = generator or GeneratorAgent()
        self.supported_extensions = {".py", ".js", ".ts", ".yaml", ".yml", ".json", ".md", ".sql"}

    async def scan_environment(self, root_path: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Scan a directory to identify potential intelligence domains.
        """
        root = Path(root_path)
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Invalid scan path: {root_path}")

        findings = {
            "path": str(root.absolute()),
            "structure": [],
            "file_types": {},
            "content_samples": {},
            "total_files": 0
        }

        for path in root.rglob("*"):
            # Respect depth
            depth = len(path.relative_to(root).parts)
            if depth > max_depth:
                continue

            if path.is_dir():
                findings["structure"].append(f"DIR: {path.relative_to(root)}")
                continue

            findings["total_files"] += 1
            ext = path.suffix.lower()
            findings["file_types"][ext] = findings["file_types"].get(ext, 0) + 1

            # Take samples of supported files
            if ext in self.supported_extensions and len(findings["content_samples"]) < 10:
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read first 1KB
                        sample = f.read(1024)
                        findings["content_samples"][str(path.relative_to(root))] = sample
                except Exception as e:
                    logger.warning(f"Failed to read sample from {path}: {e}")

        return findings

    async def suggest_pack(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use the GeneratorAgent to suggest a Behaviour Pack based on scan results.
        """
        prompt = f"""
        You are the PersonaVault V3 Discovery Agent.
        Analyze the following environment scan results and suggest a PersonaVault Behaviour Pack.
        
        SCAN RESULTS:
        - Root: {scan_results['path']}
        - Total Files: {scan_results['total_files']}
        - Structure: {scan_results['structure'][:20]} (truncated)
        - File Types: {scan_results['file_types']}
        
        CONTENT SAMPLES:
        {json.dumps(scan_results['content_samples'], indent=2)}
        
        GOAL:
        1. Identify the logical "Domain" of this environment (e.g., procurement, security, healthcare).
        2. Propose a Behaviour Pack name and version.
        3. Draft 3-5 high-level Policies that would be relevant for governing decisions in this environment.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "pack": {{
                "name": "domain-name-intelligence",
                "domain": "domain",
                "version": "1.0.0",
                "description": "Short description of what this pack governs"
            }},
            "policies": [
                {{
                    "name": "Policy Name",
                    "description": "What it does",
                    "conditions": ["condition1", "condition2"],
                    "actions": ["action1"]
                }}
            ]
        }}
        """

        # Using GeneratorAgent to get the suggestion
        # In a real environment, we'd use the internal generator reasoning
        response = await self.generator.generate(
            query=prompt,
            context=[],
            provider="ollama" # Default for discovery
        )

        try:
            # Attempt to parse JSON from the response
            text = response.get("answer", "")
            # Simple extractor for JSON blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "{" in text:
                text = text[text.find("{"):text.rfind("}")+1]
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse pack suggestion: {e}")
            return {
                "error": "Failed to parse discovery logic",
                "raw_response": response.get("answer")
            }

discovery_service = DiscoveryService()
