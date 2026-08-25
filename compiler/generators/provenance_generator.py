from jinja2 import Environment
from typing import Dict

class ProvenanceGenerator:
    def __init__(self, template_env: Environment):
        self.template_env = template_env
        
    def generate(self, provenance_config: Dict, version: str = "1.0.0", **kwargs) -> str:
        template = self.template_env.get_template("provenance_tracker.py.j2")
        return template.render(provenance_config=provenance_config, version=version, **kwargs)
