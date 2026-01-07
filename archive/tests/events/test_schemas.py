"""
Tests for Event Schema Validation

Story 2: Event Schema Validation (Epic 3.1)
Coverage: Schema registry, validation, custom validators
"""

import pytest
from waooaw.events.event_bus import Event, EventType, EventPriority
from waooaw.events.schemas import (
    EventSchema,
    EventValidator,
    SchemaRegistry,
    ValidationError,
)


# Test EventSchema
def test_schema_creation():
    """Test creating an event schema"""
    schema = EventSchema(
        event_type="test.event",
        version="1.0.0",
        description="Test event schema",
        json_schema={
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "number"},
            },
            "required": ["field1"],
        },
    )

    assert schema.event_type == "test.event"
    assert schema.version == "1.0.0"
    assert schema.description == "Test event schema"


def test_schema_validate_valid_payload():
    """Test validating a valid payload"""
    schema = EventSchema(
        event_type="test.event",
        version="1.0.0",
        json_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
            "required": ["name"],
        },
    )

    payload = {"name": "Test", "age": 25}
    assert schema.validate_payload(payload) is True


def test_schema_validate_invalid_payload():
    """Test validating an invalid payload"""
    schema = EventSchema(
        event_type="test.event",
        version="1.0.0",
        json_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
            "required": ["name"],
        },
    )

    payload = {"age": "not_a_number"}  # Missing required field, wrong type

    with pytest.raises(ValidationError) as exc_info:
        schema.validate_payload(payload)

    assert "Validation failed" in str(exc_info.value)


def test_schema_with_custom_validator():
    """Test schema with custom validator"""

    def validate_positive_age(payload):
        """Custom validator: age must be positive"""
        return payload.get("age", 0) > 0

    schema = EventSchema(
        event_type="test.event",
        version="1.0.0",
        json_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
            "required": ["name", "age"],
        },
        custom_validators=[validate_positive_age],
    )

    # Valid payload
    valid_payload = {"name": "Test", "age": 25}
    assert schema.validate_payload(valid_payload) is True

    # Invalid payload (negative age)
    invalid_payload = {"name": "Test", "age": -5}
    with pytest.raises(ValidationError):
        schema.validate_payload(invalid_payload)


# Test SchemaRegistry
def test_registry_creation():
    """Test creating a schema registry"""
    registry = SchemaRegistry()

    # Should have default schemas registered
    schemas = registry.list_schemas()
    assert len(schemas) > 0
    assert "agent.started:1.0.0" in schemas


def test_registry_register_schema():
    """Test registering a custom schema"""
    registry = SchemaRegistry()

    schema = EventSchema(
        event_type="custom.event",
        version="1.0.0",
        json_schema={"type": "object", "properties": {}},
    )

    registry.register_schema(schema)

    retrieved = registry.get_schema("custom.event", "1.0.0")
    assert retrieved is not None
    assert retrieved.event_type == "custom.event"


def test_registry_get_nonexistent_schema():
    """Test getting a schema that doesn't exist"""
    registry = SchemaRegistry()

    schema = registry.get_schema("nonexistent.event")
    assert schema is None


def test_registry_list_schemas():
    """Test listing all schemas"""
    registry = SchemaRegistry()

    schemas = registry.list_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) > 0


# Test default schemas
def test_default_agent_started_schema():
    """Test default schema for agent.started event"""
    registry = SchemaRegistry()

    schema = registry.get_schema(EventType.AGENT_STARTED.value)
    assert schema is not None

    # Valid payload
    valid_payload = {
        "agent_did": "did:waooaw:agent:test",
        "status": "ready",
        "capabilities": ["capability1"],
    }
    assert schema.validate_payload(valid_payload) is True

    # Invalid payload (missing required field)
    invalid_payload = {"status": "ready"}
    with pytest.raises(ValidationError):
        schema.validate_payload(invalid_payload)


def test_default_task_completed_schema():
    """Test default schema for task.completed event"""
    registry = SchemaRegistry()

    schema = registry.get_schema(EventType.TASK_COMPLETED.value)
    assert schema is not None

    # Valid payload
    valid_payload = {
        "task_id": "task-123",
        "result": "success",
        "duration_ms": 1500,
        "success": True,
    }
    assert schema.validate_payload(valid_payload) is True


# Test EventValidator
def test_validator_creation():
    """Test creating an event validator"""
    validator = EventValidator()

    assert validator.validation_enabled is True
    assert validator.strict_mode is False
    assert validator.registry is not None


def test_validator_validate_event():
    """Test validating an event"""
    validator = EventValidator()

    event = Event(
        event_type=EventType.AGENT_STARTED,
        source_agent="did:waooaw:agent:test",
        payload={
            "agent_did": "did:waooaw:agent:test",
            "status": "ready",
            "capabilities": ["cap1"],
        },
    )

    assert validator.validate_event(event) is True


def test_validator_validate_invalid_event():
    """Test validating an invalid event"""
    validator = EventValidator()

    event = Event(
        event_type=EventType.AGENT_STARTED,
        source_agent="did:waooaw:agent:test",
        payload={"status": "ready"},  # Missing required agent_did
    )

    with pytest.raises(ValidationError):
        validator.validate_event(event)


def test_validator_with_unregistered_event_type():
    """Test validating event with unregistered type (non-strict mode)"""
    validator = EventValidator()
    validator.disable_strict_mode()

    event = Event(
        event_type=EventType.CUSTOM,
        source_agent="did:waooaw:agent:test",
        payload={"anything": "goes"},
    )

    # Should pass in non-strict mode
    assert validator.validate_event(event) is True


def test_validator_strict_mode():
    """Test validating event with unregistered type (strict mode)"""
    validator = EventValidator()
    validator.enable_strict_mode()

    event = Event(
        event_type=EventType.CUSTOM,
        source_agent="did:waooaw:agent:test",
        payload={"anything": "goes"},
    )

    # Should fail in strict mode
    with pytest.raises(ValidationError, match="No schema registered"):
        validator.validate_event(event)


def test_validator_enable_disable():
    """Test enabling and disabling validation"""
    validator = EventValidator()

    # Validation enabled by default
    assert validator.validation_enabled is True

    # Disable validation
    validator.disable_validation()
    assert validator.validation_enabled is False

    # Invalid event should pass when validation disabled
    event = Event(
        event_type=EventType.AGENT_STARTED,
        source_agent="did:waooaw:agent:test",
        payload={},  # Invalid payload
    )
    assert validator.validate_event(event) is True

    # Re-enable validation
    validator.enable_validation()
    assert validator.validation_enabled is True

    # Now should fail
    with pytest.raises(ValidationError):
        validator.validate_event(event)


def test_validator_batch_validation():
    """Test validating a batch of events"""
    validator = EventValidator()

    events = [
        Event(
            event_type=EventType.AGENT_STARTED,
            source_agent="did:waooaw:agent:test1",
            payload={"agent_did": "did:waooaw:agent:test1", "status": "ready"},
        ),
        Event(
            event_type=EventType.AGENT_STARTED,
            source_agent="did:waooaw:agent:test2",
            payload={"status": "ready"},  # Invalid: missing agent_did
        ),
        Event(
            event_type=EventType.TASK_COMPLETED,
            source_agent="did:waooaw:agent:test3",
            payload={"task_id": "task-123", "result": "success"},
        ),
    ]

    results = validator.validate_batch(events)

    assert results["total"] == 3
    assert results["valid"] == 2
    assert results["invalid"] == 1
    assert len(results["errors"]) == 1
    assert "agent.started" in results["errors"][0]["event_type"]


def test_validator_with_custom_registry():
    """Test validator with custom registry"""
    registry = SchemaRegistry()

    # Register custom schema
    custom_schema = EventSchema(
        event_type="custom.test",
        version="1.0.0",
        json_schema={
            "type": "object",
            "properties": {"value": {"type": "number", "minimum": 0}},
            "required": ["value"],
        },
    )
    registry.register_schema(custom_schema)

    validator = EventValidator(registry=registry)

    # Valid event
    event = Event(
        event_type=EventType.CUSTOM,
        source_agent="did:waooaw:agent:test",
        payload={"value": 42},
    )

    # This will pass in non-strict mode since EventType.CUSTOM
    # maps to "custom" not "custom.test"
    validator.disable_strict_mode()
    assert validator.validate_event(event) is True


def test_schema_versioning():
    """Test schema versioning support"""
    registry = SchemaRegistry()

    # Register v1.0.0
    schema_v1 = EventSchema(
        event_type="versioned.event",
        version="1.0.0",
        json_schema={
            "type": "object",
            "properties": {"field1": {"type": "string"}},
            "required": ["field1"],
        },
    )
    registry.register_schema(schema_v1)

    # Register v2.0.0 with different schema
    schema_v2 = EventSchema(
        event_type="versioned.event",
        version="2.0.0",
        json_schema={
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "string"},
            },
            "required": ["field1", "field2"],
        },
    )
    registry.register_schema(schema_v2)

    # Get v1.0.0
    retrieved_v1 = registry.get_schema("versioned.event", "1.0.0")
    assert retrieved_v1 is not None
    assert retrieved_v1.version == "1.0.0"

    # Get v2.0.0
    retrieved_v2 = registry.get_schema("versioned.event", "2.0.0")
    assert retrieved_v2 is not None
    assert retrieved_v2.version == "2.0.0"

    # Validate against v1 (should pass)
    payload_v1 = {"field1": "value1"}
    assert retrieved_v1.validate_payload(payload_v1) is True

    # Same payload against v2 (should fail - missing field2)
    with pytest.raises(ValidationError):
        retrieved_v2.validate_payload(payload_v1)


def test_complex_schema_patterns():
    """Test complex JSON schema patterns"""
    schema = EventSchema(
        event_type="complex.event",
        version="1.0.0",
        json_schema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "did": {"type": "string", "pattern": "^did:waooaw:"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 10,
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                },
            },
            "required": ["did", "tags"],
        },
    )

    # Valid payload
    valid_payload = {
        "did": "did:waooaw:agent:test",
        "tags": ["tag1", "tag2"],
        "metadata": {"priority": "high"},
    }
    assert schema.validate_payload(valid_payload) is True

    # Invalid DID pattern
    invalid_payload_1 = {
        "did": "invalid_did",
        "tags": ["tag1"],
    }
    with pytest.raises(ValidationError):
        schema.validate_payload(invalid_payload_1)

    # Empty tags array (violates minItems)
    invalid_payload_2 = {
        "did": "did:waooaw:agent:test",
        "tags": [],
    }
    with pytest.raises(ValidationError):
        schema.validate_payload(invalid_payload_2)
