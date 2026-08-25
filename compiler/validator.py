"""
Pack Validator - Ensures YAML packs meet schema requirements
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"  # error, warning, info


class PackValidator:
    """Validate behavior pack YAML schema"""
    
    REQUIRED_FIELDS = ['pack', 'entities', 'events', 'policies']
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate(self, pack_data: Dict[str, Any]) -> bool:
        """Validate pack data, returns True if valid"""
        self.errors = []
        self.warnings = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in pack_data:
                self.errors.append(ValidationError(
                    field=field,
                    message=f"Missing required field: {field}"
                ))
                return False
        
        # Validate pack metadata
        self._validate_pack_meta(pack_data['pack'])
        
        # Validate entities
        self._validate_entities(pack_data.get('entities', {}))
        
        # Validate events
        self._validate_events(pack_data.get('events', {}))
        
        # Validate policies
        self._validate_policies(
            pack_data.get('policies', []),
            pack_data.get('entities', {})
        )
        
        # Log validation results
        if self.errors:
            for err in self.errors:
                logger.error(f"❌ Validation Error: {err.field} - {err.message}")
            return False
        
        if self.warnings:
            for warn in self.warnings:
                logger.warning(f"⚠️ {warn.field} - {warn.message}")
        
        logger.info("✅ Pack validation passed")
        return True
    
    def _validate_pack_meta(self, meta: Dict[str, Any]):
        """Validate pack metadata"""
        required = ['name', 'domain', 'version']
        
        for field in required:
            if field not in meta:
                self.errors.append(ValidationError(
                    field=f"pack.{field}",
                    message=f"Missing required metadata field: {field}"
                ))
    
    def _validate_entities(self, entities: Dict[str, Any]):
        """Validate entity definitions"""
        for entity_name, entity_def in entities.items():
            if not isinstance(entity_def, dict):
                self.errors.append(ValidationError(
                    field=f"entities.{entity_name}",
                    message="Entity must be a dictionary"
                ))
                continue
            
            # Check fields
            if 'fields' not in entity_def:
                self.warnings.append(ValidationError(
                    field=f"entities.{entity_name}",
                    message="No fields defined for entity",
                    severity="warning"
                ))
                continue
            
            for field_name, field_type in entity_def['fields'].items():
                if field_type not in ['string', 'number', 'boolean', 'date', 'array', 'object']:
                    self.warnings.append(ValidationError(
                        field=f"entities.{entity_name}.fields.{field_name}",
                        message=f"Unknown field type: {field_type}",
                        severity="warning"
                    ))
    
    def _validate_events(self, events: Dict[str, Any]):
        """Validate event definitions"""
        for event_name, event_def in events.items():
            if not isinstance(event_def, dict):
                self.errors.append(ValidationError(
                    field=f"events.{event_name}",
                    message="Event must be a dictionary"
                ))
                continue
            
            # Check fields
            if 'fields' not in event_def:
                self.warnings.append(ValidationError(
                    field=f"events.{event_name}",
                    message="No fields defined for event",
                    severity="warning"
                ))
    
    def _validate_policies(self, policies: List[Dict], entities: Dict[str, Any]):
        """Validate policy definitions"""
        for idx, policy in enumerate(policies):
            policy_name = policy.get('name', f'policy_{idx}')
            
            # Check required fields
            required = ['name', 'when', 'decision', 'actions', 'autonomy']
            for field in required:
                if field not in policy:
                    self.errors.append(ValidationError(
                        field=f"policies[{idx}].{field}",
                        message=f"Missing required policy field: {field}"
                    ))
                    continue
            
            # Validate signals
            signals = policy.get('when', {}).get('signals', [])
            for signal in signals:
                if not isinstance(signal, str):
                    self.errors.append(ValidationError(
                        field=f"policies[{idx}].when.signals",
                        message=f"Signal must be string, got {type(signal)}"
                    ))
                elif signal not in entities:
                    self.warnings.append(ValidationError(
                        field=f"policies[{idx}].when.signals.{signal}",
                        message=f"Signal '{signal}' not found in entities",
                        severity="warning"
                    ))
            
            # Validate autonomy
            autonomy = policy.get('autonomy', {}).get('level', '')
            if autonomy not in ['observe', 'suggest', 'recommend', 'approve', 'execute']:
                self.errors.append(ValidationError(
                    field=f"policies[{idx}].autonomy.level",
                    message=f"Invalid autonomy level: {autonomy}. Must be one of: observe, suggest, recommend, approve, execute"
                ))
            
            # Validate confidence threshold
            threshold = policy.get('confidence_threshold', 0.0)
            if not 0.0 <= threshold <= 1.0:
                self.errors.append(ValidationError(
                    field=f"policies[{idx}].confidence_threshold",
                    message=f"Confidence threshold must be between 0.0 and 1.0, got {threshold}"
                ))
