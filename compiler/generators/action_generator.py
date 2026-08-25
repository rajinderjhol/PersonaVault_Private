from jinja2 import Environment
from typing import List, Dict

class ActionGenerator:
    def __init__(self, template_env: Environment):
        self.template_env = template_env
        
    def generate(self, actions: List[Dict], **kwargs) -> str:
        template = self.template_env.get_template("action_mapper.py.j2")
        return template.render(actions=actions, **kwargs)
