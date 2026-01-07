"""
Event Schema Validation

Story 2: Event Schema Validation (Epic 3.1)
Points: 3

Ensures all events conform to defined schemas for data quality and consistency.
Provides a registry for event types and their validation rules.

Features:
- JSON schema validation for event payloads
- Event type registry with schema definitions
- Validation pipeline for publish/subscribe
- Custom validators for domain-specific rules
- Schema versioning support
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError

from waooaw.events.event_bus import Event, EventType

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Event validation failed"""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


@dataclass
class EventSchema:
    """
    Schema definition for an event type.

    Contains JSON schema for payload validation and optional custom validators.
    """

    event_type: str
    version: str
    json_schema: Dict[str, Any]
    description: str = ""
    custom_validators: List[Callable[[Dict[str, Any]], bool]] = field(
        default_factory=list
    )

    def validate_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate payload against JSON schema and custom validators.

        Args:
            payload: Event payload to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        # JSON schema validation
        try:
            validate(instance=payload, schema=self.json_schema)
        except JsonSchemaValidationError as e:
            errors.append(f"JSON schema error: {e.message}")

        # Custom validators
        for validator in self.custom_validators:
            try:
                if not validator(payload):
                    errors.append(f"Custom validation failed: {validator.__name__}")
            except Exception as e:
                errors.append(f"Custom validator error ({validator.__name__}): {e}")

        if errors:
            raise ValidationError(
                f"Validation failed for {self.event_type}", errors=errors
            )

        return True


class SchemaRegistry:
    """
    Registry for event schemas.

    Stores and retrieves schemas for different event types.
    Supports schema versioning.
    """

    def __init__(self):
        self.schemas: Dict[str, EventSchema] = {}
        self._initialize_default_schemas()

    def register_schema(self, schema: EventSchema) -> None:
        """
        Register an event schema.

        Args:
            schema: Schema to register
        """
        key = f"{schema.event_type}:{schema.version}"
        self.schemas[key] = schema
        logger.info(f"Registered schema: {key}")

    def get_schema(
        self, event_type: str, version: str = "1.0.0"
    ) -> Optional[EventSchema]:
        """
        Get schema for event type and version.

        Args:
            event_type: Event type to get schema for
            version: Schema version (default: 1.0.0)

        Returns:
            EventSchema if found, None otherwise
        """
        key = f"{event_type}:{version}"
        return self.schemas.get(key)

    def list_schemas(self) -> List[str]:
        """
        List all registered schema keys.

        Returns:
            List of schema keys (event_type:version)
        """
        return list(self.schemas.keys())

    def _initialize_default_schemas(self) -> None:
        """Initialize default schemas for standard event types"""

        # Agent lifecycle schemas
        self.register_schema(
            EventSchema(
                event_type=EventType.AGENT_STARTED.value,
                version="1.0.0",
                description="Agent started event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "agent_did": {"type": "string", "pattern": "^did:waooaw:"},
                        "agent_type": {"type": "string"},
                        "capabilities": {"type": "array", "items": {"type": "string"}},
                        "status": {"type": "string", "enum": ["ready", "initializing"]},
                    },
                    "required": ["agent_did", "status"],
                },
            )
        )

        self.register_schema(
            EventSchema(
                event_type=EventType.AGENT_STOPPED.value,
                version="1.0.0",
                description="Agent stopped event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "agent_did": {"type": "string", "pattern": "^did:waooaw:"},
                        "reason": {"type": "string"},
                        "graceful": {"type": "boolean"},
                    },
                    "required": ["agent_did"],
                },
            )
        )

        # Task schemas
        self.register_schema(
            EventSchema(
                event_type=EventType.TASK_CREATED.value,
                version="1.0.0",
                description="Task created event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "task_type": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
                        "assigned_to": {"type": "string"},
                        "deadline": {"type": "string", "format": "date-time"},
                    },
                    "required": ["task_id", "task_type"],
                },
            )
        )

        self.register_schema(
            EventSchema(
                event_type=EventType.TASK_COMPLETED.value,
                version="1.0.0",
                description="Task completed event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "result": {"type": "string"},
                        "duration_ms": {"type": "number", "minimum": 0},
                        "success": {"type": "boolean"},
                    },
                    "required": ["task_id", "result"],
                },
            )
        )

        # Capability schemas
        self.register_schema(
            EventSchema(
                event_type=EventType.CAPABILITY_INVOKED.value,
                version="1.0.0",
                description="Capability invoked event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "capability_id": {"type": "string"},
                        "agent_did": {"type": "string"},
                        "input": {"type": "object"},
                        "invocation_id": {"type": "string"},
                    },
                    "required": ["capability_id", "agent_did"],
                },
            )
        )

        # Consciousness schemas
        self.register_schema(
            EventSchema(
                event_type=EventType.CONSCIOUSNESS_WAKE.value,
                version="1.0.0",
                description="Agent consciousness wake event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "agent_did": {"type": "string", "pattern": "^did:waooaw:"},
                        "session_id": {"type": "string"},
                        "attestation": {"type": "object"},
                    },
                    "required": ["agent_did"],
                },
            )
        )

        # System schemas
        self.register_schema(
            EventSchema(
                event_type=EventType.SYSTEM_ALERT.value,
                version="1.0.0",
                description="System alert event",
                json_schema={
                    "type": "object",
                    "properties": {
                        "alert_type": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "message": {"type": "string"},
                        "component": {"type": "string"},
                        "timestamp": {"type": "string"},
                    },
                    "required": ["alert_type", "severity", "message"],
                },
            )
        )


class EventValidator:
    """
    Validates events against registered schemas.

    Integrates with EventBus to ensure all published events are valid.
    """

    def __init__(self, registry: Optional[SchemaRegistry] = None):
        self.registry = registry or SchemaRegistry()
        self.validation_enabled = True
        self.strict_mode = False  # If True, reject events without schemas

    def validate_event(self, event: Event) -> bool:
        """
        Validate an event against its schema.

        Args:
            event: Event to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not self.validation_enabled:
            return True

        # Get event type
        event_type = (
            event.event_type.value
            if isinstance(event.event_type, EventType)
            else event.event_type
        )

        # Get schema
        schema = self.registry.get_schema(event_type)

        if schema is None:
            if self.strict_mode:
                raise ValidationError(
                    f"No schema registered for event type: {event_type}"
                )
            else:
                # Allow unregistered event types in non-strict mode
                logger.warning(f"No schema found for event type: {event_type}")
                return True

        # Validate payload
        try:
            schema.validate_payload(event.payload)
            logger.debug(f"✅ Event validated: {event_type}")
            return True
        except ValidationError as e:
            logger.error(f"❌ Event validation failed: {str(e)}")
            logger.error(f"Errors: {e.errors}")
            raise

    def validate_batch(self, events: List[Event]) -> Dict[str, Any]:
        """
        Validate a batch of events.

        Args:
            events: List of events to validate

        Returns:
            Dictionary with validation results
        """
        results = {
            "total": len(events),
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }

        for event in events:
            try:
                self.validate_event(event)
                results["valid"] += 1
            except ValidationError as e:
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "event_id": event.event_id,
                        "event_type": (
                            event.event_type.value
                            if isinstance(event.event_type, EventType)
                            else event.event_type
                        ),
                        "message": str(e),
                        "errors": e.errors,
                    }
                )

        return results

    def enable_validation(self) -> None:
        """Enable event validation"""
        self.validation_enabled = True
        logger.info("Event validation enabled")

    def disable_validation(self) -> None:
        """Disable event validation (use with caution)"""
        self.validation_enabled = False
        logger.warning("⚠️  Event validation disabled")

    def enable_strict_mode(self) -> None:
        """
        Enable strict mode.

        In strict mode, events without registered schemas are rejected.
        """
        self.strict_mode = True
        logger.info("Strict validation mode enabled")

    def disable_strict_mode(self) -> None:
        """
        Disable strict mode.

        In non-strict mode, events without schemas are allowed with a warning.
        """
        self.strict_mode = False
        logger.info("Strict validation mode disabled")
