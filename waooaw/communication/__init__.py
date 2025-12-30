"""
Communication Module - WowCommunication Agent

Epic 3.2: Inter-Agent Protocol (Theme 3 TODDLER)

The communication module provides direct agent-to-agent messaging:
- Point-to-point messaging (send, receive)
- Request-response pattern (ask, reply)
- Async message delivery with retries
- Message audit trail for compliance
- Rate limiting and quota enforcement
- Multiple serialization formats (JSON, Protobuf)

This complements WowEvent (pub/sub) by enabling direct, synchronous
communication patterns between agents with guaranteed delivery.

Version: 0.7.0-dev
"""

from waooaw.communication.messaging import (
    MessageBus,
    Message,
    MessageType,
    MessagePriority,
    MessageStatus,
    DeliveryReceipt,
)
from waooaw.communication.request_response import (
    RequestResponseHandler,
    Request,
    Response,
    ResponseStatus,
    TimeoutError,
)
from waooaw.communication.audit import (
    MessageAuditTrail,
    MessageAuditLog,
    RetentionPolicy,
    AuditQuery,
    AuditStatistics,
)
from waooaw.communication.rate_limiter import (
    RateLimiter,
    TokenBucket,
    SlidingWindowCounter,
    RateLimitConfig,
    RateLimitStatus,
    RateLimitWindow,
    RateLimitExceeded,
)
from waooaw.communication.serialization import (
    MessageSerializer,
    SerializedMessage,
    Serializer,
    JSONSerializer,
    MessagePackSerializer,
    SerializationFormat,
    CompressionType,
    SerializationError,
    DeserializationError,
)

__version__ = "0.7.0-dev"

__all__ = [
    "MessageBus",
    "Message",
    "MessageType",
    "MessagePriority",
    "MessageStatus",
    "DeliveryReceipt",
    "RequestResponseHandler",
    "Request",
    "Response",
    "ResponseStatus",
    "TimeoutError",
    "MessageAuditTrail",
    "MessageAuditLog",
    "RetentionPolicy",
    "AuditQuery",
    "AuditStatistics",
]
