import yaml
import jinja2
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import shutil
import re

# Assuming standard project structure
# Replace imports as necessary for your local env
# from app.compiler.models import CompiledPack, PackValidationResult

# Mocking these for now if not available in project structure
class CompiledPack:
    def __init__(self, name, version, domain, policies, agents, patterns, runtime_code, target, manifest, signature, compiled_at):
        self.name = name
        self.version = version
        self.domain = domain
        self.policies = policies
        self.agents = agents
        self.patterns = patterns
        self.runtime_code = runtime_code
        self.target = target
        self.manifest = manifest
        self.signature = signature
        self.compiled_at = compiled_at

class PackValidationResult:
    def __init__(self, is_valid, errors=None, warnings=None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

class CompilerError(Exception): pass

class BehaviorPackCompiler:
    """
    Compiles Behavior Packs into optimized runtime code.
    
    Supports two modes:
    1. File Mode: Single YAML file (legacy behavior packs)
    2. Directory Mode: Full Domain Intelligence Unit (DIU)
    """
    
    def __init__(self, template_dir: Path = Path("app/compiler/templates")):
        self.template_dir = template_dir
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True
        )
        self.logger = logging.getLogger(__name__)
    
    async def compile(
        self, 
        source_path: Path, 
        target: str = "cloud",
        output_dir: Optional[Path] = None,
        sign_key: Optional[Path] = None
    ) -> CompiledPack:
        """
        Compile a behavior pack or Domain Intelligence Unit.
        """
        # Detect if source is a DIU directory or single YAML
        if source_path.is_dir():
            return await self._compile_diu(
                diu_path=source_path,
                target=target,
                output_dir=output_dir,
                sign_key=sign_key
            )
        else:
            return await self._compile_single_yaml(
                yaml_path=source_path,
                target=target,
                output_dir=output_dir
            )
    
    async def _compile_diu(
        self,
        diu_path: Path,
        target: str,
        output_dir: Optional[Path],
        sign_key: Optional[Path]
    ) -> CompiledPack:
        """
        Compile a Domain Intelligence Unit (DIU) from a directory.
        """
        self.logger.info(f"Compiling DIU from: {diu_path}")
        
        # 1. Validate DIU structure
        validation = await self._validate_diu_structure(diu_path)
        if not validation.is_valid:
            raise CompilerError(f"Invalid DIU structure: {validation.errors}")
        
        # 2. Load configuration
        config_path = diu_path / "pack.yaml"
        config = await self._load_config(config_path)
        self.logger.info(f"Loaded DIU config: {config.get('name')} v{config.get('version')}")
        
        # 3. Recursively load all policies
        policies = await self._load_policies(diu_path / "policies")
        self.logger.info(f"Loaded {len(policies)} policies")
        
        # 4. Bundle agent definitions
        agents = await self._bundle_agents(diu_path / "agents", config.get("agents", []))
        self.logger.info(f"Bundled {len(agents)} agents")
        
        # 5. Load crystallized patterns
        patterns = await self._load_crystallized_patterns(diu_path / "crystallized")
        self.logger.info(f"Loaded {len(patterns)} crystallized patterns")
        
        # 6. Generate runtime code using jinja2
        runtime_code = await self._generate_diu_runtime(
            config=config,
            policies=policies,
            agents=agents,
            patterns=patterns,
            target=target
        )
        
        # 7. Validate target compatibility
        await self._validate_target_compatibility(agents, patterns, target)
        
        # 8. Compile to output
        if output_dir:
            output_path = output_dir / f"{config['name']}_runtime.py"
            output_path.write_text(runtime_code)
            self.logger.info(f"Written runtime to: {output_path}")
            
            # Copy supporting files
            await self._bundle_supporting_files(diu_path, output_dir, config)
            
            # Generate manifest
            manifest = await self._generate_manifest(
                config=config,
                policies=policies,
                agents=agents,
                patterns=patterns,
                target=target,
                output_path=output_path
            )
            (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        
        # 9. Cryptographic signing (if key provided)
        signature = None
        if sign_key and output_dir:
            # Placeholder for actual signing logic as implemented in user suggestion
            self.logger.info("Signing DIU (placeholder)")
            signature = "mock_signature_for_implementation"
        
        return CompiledPack(
            name=config.get("name"),
            version=config.get("version"),
            domain=config.get("domain"),
            policies=policies,
            agents=agents,
            patterns=patterns,
            runtime_code=runtime_code,
            target=target,
            manifest=None, # Simplified for mock
            signature=signature,
            compiled_at=datetime.now()
        )
    
    async def _validate_diu_structure(self, diu_path: Path) -> PackValidationResult:
        errors = []
        warnings = []
        if not (diu_path / "pack.yaml").exists():
            errors.append("pack.yaml is required")
        if not (diu_path / "policies").is_dir():
            errors.append("policies/ directory is required")
        return PackValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    async def _load_config(self, config_path: Path) -> Dict[str, Any]:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    async def _load_policies(self, policy_dir: Path) -> Dict[str, Any]:
        policies = {}
        for yaml_file in policy_dir.glob("*.yaml"):
            with open(yaml_file, 'r') as f:
                policies[yaml_file.stem] = yaml.safe_load(f)
        return policies
    
    async def _bundle_agents(self, agent_dir: Path, agent_configs: List[Dict]) -> Dict[str, Any]:
        agents = {}
        for agent_config in agent_configs:
            agent_class = agent_config.get("class")
            if not agent_class: continue
            agent_file = agent_dir / f"{agent_class}.py"
            agents[agent_class] = {
                "code": agent_file.read_text(),
                "config": agent_config
            }
        return agents
    
    async def _load_crystallized_patterns(self, pattern_dir: Path) -> List[Dict[str, Any]]:
        patterns = []
        for json_file in pattern_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                patterns.append(json.load(f))
        return patterns
    
    async def _generate_diu_runtime(self, config, policies, agents, patterns, target) -> str:
        template = self.jinja_env.get_template("diu_runtime.py.j2")
        context = {
            "config": config,
            "policies": policies,
            "agents": agents,
            "patterns": patterns,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "policy_count": len(policies),
            "agent_count": len(agents),
            "pattern_count": len(patterns)
        }
        return template.render(**context)

    async def _validate_target_compatibility(self, agents, patterns, target): pass
    async def _generate_manifest(self, config, policies, agents, patterns, target, output_path): return {}
    async def _bundle_supporting_files(self, source_diu, output_dir, config): pass
    async def _compile_single_yaml(self, yaml_path, target, output_dir): raise NotImplementedError("File mode not yet migrated")
