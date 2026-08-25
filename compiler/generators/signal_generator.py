from jinja2 import Environment

class SignalGenerator:
    def __init__(self, template_env: Environment):
        self.template_env = template_env
        
    def generate(self, entities: dict, events: dict, **kwargs) -> str:
        template = self.template_env.get_template("signal_normalizer.py.j2")
        return template.render(entities=entities, events=events, **kwargs)
