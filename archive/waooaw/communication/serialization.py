"""
Message Serialization for Inter-Agent Communication

Provides pluggable serialization strategies with compression support.
Optimizes message size for network efficiency and storage.

Supported Formats:
- JSON: Human-readable, default format
- MessagePack: Binary, compact, fast
- Protobuf: Schema-based, smallest size (future)
- Compression: gzip, zlib for large payloads

Features:
- Pluggable serializers (register custom formats)
- Automatic compression threshold
- Content negotiation
- Schema validation
"""

import gzip
import json
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Type

try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


class SerializationFormat(Enum):
    """Supported serialization formats."""
    
    JSON = "json"
    MSGPACK = "msgpack"
    PROTOBUF = "protobuf"


class CompressionType(Enum):
    """Compression algorithms."""
    
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"


@dataclass
class SerializedMessage:
    """Serialized message with metadata."""
    
    data: bytes
    format: SerializationFormat
    compression: CompressionType
    original_size: int
    compressed_size: int
    
    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size


class SerializationError(Exception):
    """Raised when serialization fails."""
    pass


class DeserializationError(Exception):
    """Raised when deserialization fails."""
    pass


class Serializer(ABC):
    """Base serializer interface."""
    
    @abstractmethod
    def serialize(self, data: Dict[str, Any]) -> bytes:
        """
        Serialize data to bytes.
        
        Args:
            data: Dictionary to serialize
            
        Returns:
            Serialized bytes
            
        Raises:
            SerializationError: If serialization fails
        """
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """
        Deserialize bytes to data.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized dictionary
            
        Raises:
            DeserializationError: If deserialization fails
        """
        pass
    
    @property
    @abstractmethod
    def format(self) -> SerializationFormat:
        """Get serialization format."""
        pass


class JSONSerializer(Serializer):
    """JSON serializer (default)."""
    
    def serialize(self, data: Dict[str, Any]) -> bytes:
        """Serialize to JSON bytes."""
        try:
            return json.dumps(data, ensure_ascii=False).encode('utf-8')
        except (TypeError, ValueError) as e:
            raise SerializationError(f"JSON serialization failed: {e}")
    
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize from JSON bytes."""
        try:
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise DeserializationError(f"JSON deserialization failed: {e}")
    
    @property
    def format(self) -> SerializationFormat:
        return SerializationFormat.JSON


class MessagePackSerializer(Serializer):
    """MessagePack serializer (binary, compact)."""
    
    def __init__(self):
        if not MSGPACK_AVAILABLE:
            raise ImportError("msgpack not installed. Install with: pip install msgpack")
    
    def serialize(self, data: Dict[str, Any]) -> bytes:
        """Serialize to MessagePack bytes."""
        try:
            return msgpack.packb(data, use_bin_type=True)
        except Exception as e:
            raise SerializationError(f"MessagePack serialization failed: {e}")
    
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize from MessagePack bytes."""
        try:
            return msgpack.unpackb(data, raw=False, strict_map_key=False)
        except Exception as e:
            raise DeserializationError(f"MessagePack deserialization failed: {e}")
    
    @property
    def format(self) -> SerializationFormat:
        return SerializationFormat.MSGPACK


class Compressor:
    """Message compression utilities."""
    
    @staticmethod
    def compress(data: bytes, compression_type: CompressionType) -> bytes:
        """
        Compress data.
        
        Args:
            data: Data to compress
            compression_type: Compression algorithm
            
        Returns:
            Compressed bytes
        """
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(data, compresslevel=6)
        elif compression_type == CompressionType.ZLIB:
            return zlib.compress(data, level=6)
        else:
            return data
    
    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """
        Decompress data.
        
        Args:
            data: Compressed data
            compression_type: Compression algorithm
            
        Returns:
            Decompressed bytes
        """
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.decompress(data)
        elif compression_type == CompressionType.ZLIB:
            return zlib.decompress(data)
        else:
            return data


class MessageSerializer:
    """
    Message serialization manager with pluggable formats and compression.
    
    Features:
    - Multiple serialization formats
    - Automatic compression for large payloads
    - Format registration
    - Content negotiation
    """
    
    def __init__(
        self,
        default_format: SerializationFormat = SerializationFormat.JSON,
        compression_threshold: int = 1024,  # Compress if > 1KB
        default_compression: CompressionType = CompressionType.GZIP,
    ):
        """
        Initialize message serializer.
        
        Args:
            default_format: Default serialization format
            compression_threshold: Size threshold for automatic compression (bytes)
            default_compression: Default compression type
        """
        self.default_format = default_format
        self.compression_threshold = compression_threshold
        self.default_compression = default_compression
        
        # Register built-in serializers
        self.serializers: Dict[SerializationFormat, Serializer] = {
            SerializationFormat.JSON: JSONSerializer(),
        }
        
        # Register MessagePack if available
        if MSGPACK_AVAILABLE:
            self.serializers[SerializationFormat.MSGPACK] = MessagePackSerializer()
    
    def register_serializer(self, serializer: Serializer):
        """Register custom serializer."""
        self.serializers[serializer.format] = serializer
    
    def serialize(
        self,
        data: Dict[str, Any],
        format: Optional[SerializationFormat] = None,
        compression: Optional[CompressionType] = None,
    ) -> SerializedMessage:
        """
        Serialize data with optional compression.
        
        Args:
            data: Data to serialize
            format: Serialization format (uses default if None)
            compression: Compression type (auto if None)
            
        Returns:
            SerializedMessage with metadata
            
        Raises:
            SerializationError: If format not supported or serialization fails
        """
        # Get format
        format = format or self.default_format
        
        # Get serializer
        serializer = self.serializers.get(format)
        if not serializer:
            raise SerializationError(f"Unsupported format: {format}")
        
        # Serialize
        serialized = serializer.serialize(data)
        original_size = len(serialized)
        
        # Determine compression
        if compression is None:
            # Auto-compress if over threshold
            compression = (
                self.default_compression
                if original_size > self.compression_threshold
                else CompressionType.NONE
            )
        
        # Compress
        compressed = Compressor.compress(serialized, compression)
        compressed_size = len(compressed)
        
        return SerializedMessage(
            data=compressed,
            format=format,
            compression=compression,
            original_size=original_size,
            compressed_size=compressed_size,
        )
    
    def deserialize(
        self,
        message: SerializedMessage,
    ) -> Dict[str, Any]:
        """
        Deserialize message.
        
        Args:
            message: SerializedMessage to deserialize
            
        Returns:
            Deserialized data
            
        Raises:
            DeserializationError: If format not supported or deserialization fails
        """
        # Get serializer
        serializer = self.serializers.get(message.format)
        if not serializer:
            raise DeserializationError(f"Unsupported format: {message.format}")
        
        # Decompress
        decompressed = Compressor.decompress(message.data, message.compression)
        
        # Deserialize
        return serializer.deserialize(decompressed)
    
    def serialize_message_payload(
        self,
        message: Any,
        format: Optional[SerializationFormat] = None,
    ) -> tuple[bytes, SerializationFormat, CompressionType]:
        """
        Serialize message payload (convenience method).
        
        Args:
            message: Message object with to_dict() method
            format: Serialization format
            
        Returns:
            (serialized_bytes, format, compression) tuple
        """
        # Convert to dict
        if hasattr(message, 'to_dict'):
            data = message.to_dict()
        elif isinstance(message, dict):
            data = message
        else:
            raise SerializationError("Message must have to_dict() or be dict")
        
        # Serialize
        result = self.serialize(data, format=format)
        
        return result.data, result.format, result.compression
    
    def deserialize_message_payload(
        self,
        data: bytes,
        format: SerializationFormat,
        compression: CompressionType,
        message_class: Optional[Type] = None,
    ) -> Any:
        """
        Deserialize message payload (convenience method).
        
        Args:
            data: Serialized bytes
            format: Serialization format
            compression: Compression type
            message_class: Message class with from_dict() (optional)
            
        Returns:
            Deserialized message object or dict
        """
        # Create SerializedMessage
        message = SerializedMessage(
            data=data,
            format=format,
            compression=compression,
            original_size=0,  # Not needed for deserialization
            compressed_size=len(data),
        )
        
        # Deserialize
        data_dict = self.deserialize(message)
        
        # Convert to message class if provided
        if message_class and hasattr(message_class, 'from_dict'):
            return message_class.from_dict(data_dict)
        
        return data_dict
    
    def get_compression_stats(
        self,
        data: Dict[str, Any],
        formats: Optional[list[SerializationFormat]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get compression statistics for different formats.
        
        Args:
            data: Data to test
            formats: Formats to test (all available if None)
            
        Returns:
            Stats dict: {format: {size, compressed_size, ratio}}
        """
        stats = {}
        
        # Test formats
        test_formats = formats or list(self.serializers.keys())
        
        for format in test_formats:
            try:
                result = self.serialize(data, format=format)
                stats[format.value] = {
                    "original_size": result.original_size,
                    "compressed_size": result.compressed_size,
                    "compression_ratio": result.compression_ratio,
                    "compression": result.compression.value,
                }
            except Exception as e:
                stats[format.value] = {"error": str(e)}
        
        return stats
