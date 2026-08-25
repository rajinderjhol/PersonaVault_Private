from jinja2 import Environment
from typing import List, Dict

class PolicyGenerator:
    def __init__(self, template_env: Environment):
        self.template_env = template_env
        
    def generate(self, policies: List[Dict], **kwargs) -> str:
        template = self.template_env.get_template("policy_engine.py.j2")
        return template.render(policies=policies, **kwargs)
