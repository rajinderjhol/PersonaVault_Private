import uuid
from datetime import datetime
from typing import Dict, Any
from app.api.v2.models.intelligence_pack import V2IntelligencePack, PackType

class PackAdapter:
    @staticmethod
    def from_v1_behavior_pack(v1_pack: Dict[str, Any]) -> V2IntelligencePack:
        """Convert a V1 Behavior Pack to a V2 Intelligence Pack."""
        pack_id = str(uuid.uuid4())

        # Map V1 rules to V2 Policies
        policies = []
        for rule in v1_pack.get("rules", []):
            policies.append({
                "id": f"policy_{pack_id}_{len(policies)}",
                "name": rule.get("name", "Unnamed Policy"),
                "rule": rule.get("condition", ""),
                "effect": rule.get("effect", "allow"),
                "priority": rule.get("priority", 0),
                "scope": v1_pack.get("domain", "*")
            })

        # Create a default Goal and Strategy from the pack's purpose
        default_goal = {
            "id": f"goal_{pack_id}",
            "statement": f"Effectively govern {v1_pack.get('domain', 'domain')} decisions",
            "priority": 1,
            "status": "active"
        }
        default_strategy = {
            "id": f"strategy_{pack_id}",
            "goal_id": default_goal["id"],
            "name": f"{v1_pack.get('domain', 'Domain')} Strategy",
            "approach": "Apply compiled governance rules and learn from outcomes",
            "assumptions": ["Rules are correctly compiled", "Outcomes are observable"],
            "status": "active",
            "version": 1
        }

        return V2IntelligencePack(
            id=pack_id,
            name=v1_pack.get("name", "Unnamed Pack"),
            version=v1_pack.get("version", "1.0.0"),
            type=PackType.DOMAIN,
            domain=v1_pack.get("domain", "general"),
            description=v1_pack.get("description"),
            goals=[default_goal],
            strategies=[default_strategy],
            policies=policies,
            source_behavior_pack_id=v1_pack.get("id", "unknown"),
            learning_rules=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
