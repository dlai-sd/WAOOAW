"""
Vision Stack Management

Manages the 3-layer vision stack for WAOOAW platform governance.

Layers:
1. Core Vision (Immutable) - waooaw-core.yaml
2. Policies (Agent-managed) - waooaw-policies.yaml
3. Context (Ephemeral) - Runtime state

This module provides a unified interface to query and validate against
the vision stack.
"""

import json
import logging
from typing import Any, Dict, Optional
import psycopg2

logger = logging.getLogger(__name__)


class VisionStack:
    """
    Vision Stack manager for platform governance.
    
    Provides access to:
    - Layer 1: Core vision (immutable constraints)
    - Layer 2: Policies (agent-managed rules)
    - Layer 3: Context (runtime state)
    """
    
    def __init__(self, db_connection: psycopg2.extensions.connection):
        """
        Initialize vision stack.
        
        Args:
            db_connection: PostgreSQL database connection
        """
        self.db = db_connection
        
        # Load vision layers
        self.core = self._load_core_vision()
        self.policies = self._load_policies()
        self.context = self._load_context()
        
        logger.info("✅ VisionStack initialized")
    
    def _load_core_vision(self) -> Dict[str, Any]:
        """
        Load Layer 1: Core vision (immutable).
        
        In production, this would load from waooaw-core.yaml.
        For now, returns default core vision.
        """
        # TODO: Load from YAML file when it exists
        default_core = {
            'name': 'WAOOAW',
            'tagline': 'Agents Earn Your Business',
            'role': 'AI Agent Marketplace Platform',
            'constraints': [
                'NEVER generate Python code in Phase 1',
                'Always validate against vision stack',
                'Escalate ambiguous decisions to humans',
                'Preserve context across wake cycles'
            ],
            'immutable': True
        }
        
        logger.debug("Loaded core vision (default)")
        return default_core
    
    def _load_policies(self) -> Dict[str, Any]:
        """
        Load Layer 2: Policies (agent-managed).
        
        In production, this would load from waooaw-policies.yaml.
        For now, returns default policies.
        """
        # TODO: Load from YAML file when it exists
        default_policies = {
            'phase_rules': {
                'phase1_foundation': {
                    'description': 'Foundation phase - architecture and docs',
                    'file_types_allowed': ['.md', '.yaml', '.yml', '.json', '.toml', '.txt'],
                    'file_types_forbidden': ['.py'],  # Except waooaw/
                    'actions_allowed': ['documentation', 'architecture', 'planning'],
                    'actions_forbidden': ['code_generation', 'deployment']
                },
                'phase2_implementation': {
                    'description': 'Implementation phase - code and tests',
                    'file_types_allowed': ['.py', '.md', '.yaml', '.json', '.sql'],
                    'file_types_forbidden': [],
                    'actions_allowed': ['code_generation', 'testing', 'documentation'],
                    'actions_forbidden': []
                }
            },
            'documentation_rules': {
                'always_allowed': ['.md', '.markdown', '.rst', '.txt'],
                'require_review': []
            },
            'config_rules': {
                'always_allowed': ['.yaml', '.yml', '.json', '.toml', '.ini', '.env.example'],
                'forbidden': ['.env']  # Never commit secrets
            }
        }
        
        logger.debug("Loaded policies (default)")
        return default_policies
    
    def _load_context(self) -> Dict[str, Any]:
        """
        Load Layer 3: Context (runtime state).
        
        Loads current runtime context from database.
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT state_key, state_value FROM wowvision_state
            """)
            
            rows = cursor.fetchall()
            cursor.close()
            
            context = {}
            for row in rows:
                key = row[0]
                value = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                context[key] = value
            
            logger.debug(f"Loaded context with {len(context)} keys")
            return context
            
        except Exception as e:
            logger.debug(f"Could not load context: {e}")
            return {}
    
    def get_core(self) -> Dict[str, Any]:
        """Get core vision (Layer 1)"""
        return self.core
    
    def get_policies(self) -> Dict[str, Any]:
        """Get policies (Layer 2)"""
        return self.policies
    
    def get_context(self) -> Dict[str, Any]:
        """Get context (Layer 3)"""
        return self.context
    
    def validate_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate action against vision stack.
        
        Args:
            action_type: Type of action (e.g., 'create_file', 'deploy')
            action_data: Action details
        
        Returns:
            Validation result with approved/reason
        """
        # Check against core constraints
        for constraint in self.core.get('constraints', []):
            if self._violates_constraint(action_type, action_data, constraint):
                return {
                    'approved': False,
                    'reason': f'Violates core constraint: {constraint}',
                    'layer': 1
                }
        
        # Check against policies
        # (Implementation depends on action type)
        
        return {
            'approved': True,
            'reason': 'No violations found',
            'layer': 0
        }
    
    def _violates_constraint(self, action_type: str, action_data: Dict[str, Any], 
                            constraint: str) -> bool:
        """Check if action violates constraint"""
        # Implementation depends on constraint format
        # This is a simplified version
        return False
    
    def update_context(self, key: str, value: Any) -> None:
        """
        Update context (Layer 3).
        
        Args:
            key: Context key
            value: Context value
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO wowvision_state (state_key, state_value)
                VALUES (%s, %s)
                ON CONFLICT (state_key) DO UPDATE
                SET state_value = EXCLUDED.state_value
            """, (key, json.dumps(value)))
            
            self.db.commit()
            cursor.close()
            
            # Update in-memory context
            self.context[key] = value
            
            logger.debug(f"Updated context: {key}")
            
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            self.db.rollback()
