"""
Tests for Message Serialization

Tests cover:
- JSON serialization
- MessagePack serialization
- Compression (gzip, zlib)
- Pluggable serializers
- Automatic compression threshold
- Compression statistics
"""

import pytest

from waooaw.communication.serialization import (
    MessageSerializer,
    SerializedMessage,
    JSONSerializer,
    MessagePackSerializer,
    SerializationFormat,
    CompressionType,
    SerializationError,
    DeserializationError,
    MSGPACK_AVAILABLE,
)


# Test Data

@pytest.fixture
def sample_data():
    """Sample data for serialization."""
    return {
        "message_id": "msg-123",
        "from_agent": "agent-a",
        "to_agent": "agent-b",
        "type": "command",
        "payload": {
            "action": "process",
            "data": "hello world",
            "count": 42,
        },
    }


@pytest.fixture
def large_data():
    """Large data for compression testing."""
    return {
        "message_id": "msg-large",
        "payload": {
            "text": "Lorem ipsum " * 200,  # ~2.4KB
            "items": list(range(100)),
        },
    }


# JSON Serializer Tests

def test_json_serializer(sample_data):
    """Test JSON serialization."""
    serializer = JSONSerializer()
    
    # Serialize
    serialized = serializer.serialize(sample_data)
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0
    
    # Deserialize
    deserialized = serializer.deserialize(serialized)
    assert deserialized == sample_data


def test_json_serializer_format():
    """Test JSON serializer format."""
    serializer = JSONSerializer()
    assert serializer.format == SerializationFormat.JSON


def test_json_serializer_error():
    """Test JSON serialization error."""
    serializer = JSONSerializer()
    
    # Non-serializable data
    with pytest.raises(SerializationError):
        serializer.serialize({"key": object()})


def test_json_deserializer_error():
    """Test JSON deserialization error."""
    serializer = JSONSerializer()
    
    # Invalid JSON
    with pytest.raises(DeserializationError):
        serializer.deserialize(b"not json")


# MessagePack Serializer Tests

@pytest.mark.skipif(not MSGPACK_AVAILABLE, reason="msgpack not installed")
def test_msgpack_serializer(sample_data):
    """Test MessagePack serialization."""
    serializer = MessagePackSerializer()
    
    # Serialize
    serialized = serializer.serialize(sample_data)
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0
    
    # Deserialize
    deserialized = serializer.deserialize(serialized)
    assert deserialized == sample_data


@pytest.mark.skipif(not MSGPACK_AVAILABLE, reason="msgpack not installed")
def test_msgpack_serializer_format():
    """Test MessagePack serializer format."""
    serializer = MessagePackSerializer()
    assert serializer.format == SerializationFormat.MSGPACK


@pytest.mark.skipif(not MSGPACK_AVAILABLE, reason="msgpack not installed")
def test_msgpack_smaller_than_json(sample_data):
    """Test MessagePack is more compact than JSON."""
    json_ser = JSONSerializer()
    msgpack_ser = MessagePackSerializer()
    
    json_size = len(json_ser.serialize(sample_data))
    msgpack_size = len(msgpack_ser.serialize(sample_data))
    
    # MessagePack should be smaller
    assert msgpack_size < json_size


# Compression Tests

def test_compression_gzip(sample_data):
    """Test gzip compression."""
    from waooaw.communication.serialization import Compressor
    
    json_ser = JSONSerializer()
    data = json_ser.serialize(sample_data)
    
    # Compress
    compressed = Compressor.compress(data, CompressionType.GZIP)
    assert isinstance(compressed, bytes)
    
    # Decompress
    decompressed = Compressor.decompress(compressed, CompressionType.GZIP)
    assert decompressed == data


def test_compression_zlib(sample_data):
    """Test zlib compression."""
    from waooaw.communication.serialization import Compressor
    
    json_ser = JSONSerializer()
    data = json_ser.serialize(sample_data)
    
    # Compress
    compressed = Compressor.compress(data, CompressionType.ZLIB)
    assert isinstance(compressed, bytes)
    
    # Decompress
    decompressed = Compressor.decompress(compressed, CompressionType.ZLIB)
    assert decompressed == data


def test_compression_none(sample_data):
    """Test no compression."""
    from waooaw.communication.serialization import Compressor
    
    data = b"test data"
    
    # No compression
    compressed = Compressor.compress(data, CompressionType.NONE)
    assert compressed == data
    
    decompressed = Compressor.decompress(data, CompressionType.NONE)
    assert decompressed == data


# MessageSerializer Tests

def test_message_serializer_default():
    """Test MessageSerializer with default settings."""
    serializer = MessageSerializer()
    
    assert serializer.default_format == SerializationFormat.JSON
    assert serializer.compression_threshold == 1024
    assert serializer.default_compression == CompressionType.GZIP


def test_message_serializer_serialize(sample_data):
    """Test MessageSerializer serialize."""
    serializer = MessageSerializer()
    
    result = serializer.serialize(sample_data)
    
    assert isinstance(result, SerializedMessage)
    assert isinstance(result.data, bytes)
    assert result.format == SerializationFormat.JSON
    assert result.original_size > 0
    assert result.compressed_size > 0


def test_message_serializer_deserialize(sample_data):
    """Test MessageSerializer deserialize."""
    serializer = MessageSerializer()
    
    # Serialize then deserialize
    serialized = serializer.serialize(sample_data)
    deserialized = serializer.deserialize(serialized)
    
    assert deserialized == sample_data


def test_message_serializer_round_trip(sample_data):
    """Test full serialize-deserialize round trip."""
    serializer = MessageSerializer()
    
    # JSON
    result = serializer.serialize(sample_data, format=SerializationFormat.JSON)
    data = serializer.deserialize(result)
    assert data == sample_data
    
    # MessagePack (if available)
    if MSGPACK_AVAILABLE:
        result = serializer.serialize(sample_data, format=SerializationFormat.MSGPACK)
        data = serializer.deserialize(result)
        assert data == sample_data


def test_message_serializer_auto_compression(large_data):
    """Test automatic compression for large payloads."""
    serializer = MessageSerializer(compression_threshold=1000)
    
    result = serializer.serialize(large_data)
    
    # Should be compressed (over 1KB)
    assert result.compression != CompressionType.NONE
    assert result.compressed_size < result.original_size


def test_message_serializer_no_compression_small(sample_data):
    """Test no compression for small payloads."""
    serializer = MessageSerializer(compression_threshold=1024)
    
    result = serializer.serialize(sample_data)
    
    # Should not be compressed (under 1KB)
    assert result.compression == CompressionType.NONE


def test_message_serializer_force_compression(sample_data):
    """Test forcing compression on small payload."""
    serializer = MessageSerializer()
    
    result = serializer.serialize(sample_data, compression=CompressionType.GZIP)
    
    # Should be compressed even though small
    assert result.compression == CompressionType.GZIP


def test_message_serializer_compression_ratio(large_data):
    """Test compression ratio calculation."""
    serializer = MessageSerializer()
    
    result = serializer.serialize(large_data, compression=CompressionType.GZIP)
    
    assert 0 < result.compression_ratio < 1.0  # Should compress well


@pytest.mark.skipif(not MSGPACK_AVAILABLE, reason="msgpack not installed")
def test_message_serializer_msgpack_format(sample_data):
    """Test MessagePack format."""
    serializer = MessageSerializer(default_format=SerializationFormat.MSGPACK)
    
    result = serializer.serialize(sample_data)
    
    assert result.format == SerializationFormat.MSGPACK
    
    # Deserialize
    data = serializer.deserialize(result)
    assert data == sample_data


def test_message_serializer_unsupported_format(sample_data):
    """Test error on unsupported format."""
    serializer = MessageSerializer()
    
    # Protobuf not implemented
    with pytest.raises(SerializationError):
        serializer.serialize(sample_data, format=SerializationFormat.PROTOBUF)


def test_message_serializer_convenience_methods(sample_data):
    """Test convenience methods for message payloads."""
    serializer = MessageSerializer()
    
    # Serialize
    data_bytes, format, compression = serializer.serialize_message_payload(sample_data)
    
    assert isinstance(data_bytes, bytes)
    assert format == SerializationFormat.JSON
    assert isinstance(compression, CompressionType)
    
    # Deserialize
    result = serializer.deserialize_message_payload(data_bytes, format, compression)
    assert result == sample_data


def test_message_serializer_compression_stats(sample_data, large_data):
    """Test getting compression statistics."""
    serializer = MessageSerializer()
    
    # Small data
    stats = serializer.get_compression_stats(sample_data)
    
    assert "json" in stats
    assert "original_size" in stats["json"]
    assert "compressed_size" in stats["json"]
    assert "compression_ratio" in stats["json"]
    
    # Large data (better compression)
    large_stats = serializer.get_compression_stats(large_data)
    
    # Large data should compress better
    assert large_stats["json"]["compression_ratio"] < stats["json"]["compression_ratio"]


@pytest.mark.skipif(not MSGPACK_AVAILABLE, reason="msgpack not installed")
def test_compression_stats_multiple_formats(sample_data):
    """Test compression stats for multiple formats."""
    serializer = MessageSerializer()
    
    stats = serializer.get_compression_stats(sample_data)
    
    # Should have both formats
    assert "json" in stats
    assert "msgpack" in stats
    
    # MessagePack should be more compact
    assert stats["msgpack"]["original_size"] < stats["json"]["original_size"]


def test_serialized_message_properties():
    """Test SerializedMessage properties."""
    msg = SerializedMessage(
        data=b"compressed data",
        format=SerializationFormat.JSON,
        compression=CompressionType.GZIP,
        original_size=1000,
        compressed_size=500,
    )
    
    assert msg.compression_ratio == 0.5


def test_message_with_to_dict():
    """Test serializing object with to_dict method."""
    class TestMessage:
        def to_dict(self):
            return {"key": "value"}
    
    serializer = MessageSerializer()
    msg = TestMessage()
    
    data_bytes, format, compression = serializer.serialize_message_payload(msg)
    assert isinstance(data_bytes, bytes)
    
    result = serializer.deserialize_message_payload(data_bytes, format, compression)
    assert result == {"key": "value"}


def test_message_without_to_dict_error():
    """Test error when serializing unsupported object."""
    serializer = MessageSerializer()
    
    with pytest.raises(SerializationError):
        serializer.serialize_message_payload(object())


def test_register_custom_serializer(sample_data):
    """Test registering custom serializer."""
    class CustomSerializer(JSONSerializer):
        @property
        def format(self):
            return SerializationFormat.JSON  # Use JSON format ID
    
    serializer = MessageSerializer()
    custom = CustomSerializer()
    
    # Register
    serializer.register_serializer(custom)
    
    # Should work
    result = serializer.serialize(sample_data)
    assert isinstance(result, SerializedMessage)
