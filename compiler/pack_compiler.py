"""
Behavior Pack Compiler - Transforms YAML packs into executable Python
"""
import yaml
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from compiler.validator import PackValidator
from compiler.generators.signal_generator import SignalGenerator
from compiler.generators.policy_generator import PolicyGenerator
from compiler.generators.action_generator import ActionGenerator
from compiler.generators.provenance_generator import ProvenanceGenerator

logger = logging.getLogger(__name__)

class CompiledPack:
    """Container for compiled pack artifacts"""
    
    def __init__(self, name: str, domain: str, version: str):
        self.name = name
        self.domain = domain
        self.version = version
        self.signature = ""
        self.timestamp = datetime.now().isoformat()
        
        # Generated code artifacts
        self.signal_normalizer = ""
        self.policy_engine = ""
        self.action_mapper = ""
        self.provenance_tracker = ""
        self.runtime_class = ""
        
        # Metadata
        self.source_checksum = ""
        self.dependencies = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "version": self.version,
            "signature": self.signature,
            "timestamp": self.timestamp,
            "source_checksum": self.source_checksum,
            "dependencies": self.dependencies
        }
    
    def save(self, output_dir: Path):
        """Save compiled artifacts to disk"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main module
        pack_name_safe = self.name.lower().replace(' ', '_')
        with open(output_dir / f"{pack_name_safe}_pack.py", 'w') as f:
            f.write(self.runtime_class)
        
        # Save metadata
        with open(output_dir / f"{pack_name_safe}_metadata.json", 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"✅ Compiled pack: {self.name} v{self.version}")


class BehaviorPackCompiler:
    """Main compiler orchestrator"""
    
    def __init__(self, pack_dir: str = "packs/source", output_dir: str = "packs/compiled"):
        self.pack_dir = Path(pack_dir)
        self.output_dir = Path(output_dir)
        self.template_env = Environment(
            loader=FileSystemLoader("compiler/templates"),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize generators
        self.signal_generator = SignalGenerator(self.template_env)
        self.policy_generator = PolicyGenerator(self.template_env)
        self.action_generator = ActionGenerator(self.template_env)
        self.provenance_generator = ProvenanceGenerator(self.template_env)
        
        self.validator = PackValidator()
        logger.info("BehaviorPackCompiler initialized")
    
    def compile_pack(self, yaml_path: str, fixed_timestamp: Optional[str] = None) -> CompiledPack:
        """Compile a single YAML pack to Python"""
        yaml_path = Path(yaml_path)
        
        # 1. Load and validate
        logger.info(f"📦 Compiling: {yaml_path.name}")
        
        with open(yaml_path, 'r') as f:
            pack_data = yaml.safe_load(f)
        
        # Validate schema
        if not self.validator.validate(pack_data):
            raise ValueError(f"Validation failed for {yaml_path}")
        
        # Extract metadata
        pack_meta = pack_data.get('pack', {})
        compiled = CompiledPack(
            name=pack_meta.get('name', 'Unknown'),
            domain=pack_meta.get('domain', 'general'),
            version=pack_meta.get('version', '1.0.0')
        )
        if fixed_timestamp:
            compiled.timestamp = fixed_timestamp
        
        # Calculate checksum
        content_hash = hashlib.sha256(
            json.dumps(pack_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        compiled.source_checksum = content_hash
        
        # Context for generators
        gen_ctx = {
            "pack_name": compiled.name,
            "pack_name_class": compiled.name.replace(' ', '').replace('-', '_'),
            "timestamp": compiled.timestamp,
            "source_checksum": compiled.source_checksum
        }
        
        # 2. Generate signal normalizer
        compiled.signal_normalizer = self.signal_generator.generate(
            pack_data.get('entities', {}),
            pack_data.get('events', {}),
            **gen_ctx
        )
        
        # 3. Generate policy engine
        compiled.policy_engine = self.policy_generator.generate(
            pack_data.get('policies', []),
            **gen_ctx
        )
        
        # 4. Generate action mapper
        compiled.action_mapper = self.action_generator.generate(
            pack_data.get('actions', []),
            **gen_ctx
        )
        
        # 5. Generate provenance tracker
        compiled.provenance_tracker = self.provenance_generator.generate(
            pack_data.get('provenance', {}),
            version=compiled.version,
            **gen_ctx
        )
        
        # 6. Generate complete runtime class
        compiled.runtime_class = self._generate_runtime_class(compiled, pack_data)
        
        # 7. Generate signature
        compiled.signature = self._generate_signature(compiled)
        
        # 8. Save to disk
        compiled.save(self.output_dir)
        
        return compiled
    
    def _generate_runtime_class(self, compiled: CompiledPack, pack_data: dict) -> str:
        """Generate the complete runtime class"""
        template = self.template_env.get_template("pack_runtime.py.j2")
        
        pack_name_safe = compiled.name.lower().replace(' ', '_')
        pack_name_class = compiled.name.replace(' ', '').replace('-', '_')
        
        return template.render(
            pack_name=compiled.name,
            pack_name_safe=pack_name_safe,
            pack_name_class=pack_name_class,
            domain=compiled.domain,
            version=compiled.version,
            timestamp=compiled.timestamp,
            signature=compiled.signature,
            signal_normalizer=compiled.signal_normalizer,
            policy_engine=compiled.policy_engine,
            action_mapper=compiled.action_mapper,
            provenance_tracker=compiled.provenance_tracker,
            policies=pack_data.get('policies', []),
            entities=pack_data.get('entities', {}),
            events=pack_data.get('events', {}),
            autonomy_levels=pack_data.get('autonomy', {})
        )
    
    def _generate_signature(self, compiled: CompiledPack) -> str:
        """Generate a unique signature for the compiled pack based on content only"""
        content = (
            compiled.name +
            compiled.version +
            compiled.source_checksum
        )
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def compile_all(self) -> List[CompiledPack]:
        """Compile all YAML packs in the source directory"""
        compiled_packs = []
        
        if not self.pack_dir.exists():
            logger.warning(f"Source directory {self.pack_dir} does not exist.")
            return []
            
        for yaml_file in self.pack_dir.glob("*.yaml"):
            try:
                compiled = self.compile_pack(yaml_file)
                compiled_packs.append(compiled)
            except Exception as e:
                logger.error(f"❌ Failed to compile {yaml_file}: {e}")
                continue
        
        logger.info(f"✅ Compiled {len(compiled_packs)} packs")
        return compiled_packs
    
    def clean(self):
        """Clean compiled output directory"""
        import shutil
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            logger.info("🧹 Cleaned compiled packs")
