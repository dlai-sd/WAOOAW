"""
Request-Response Handler - Synchronous Communication Pattern

Provides request-response pattern on top of MessageBus:
- Send request and wait for response
- Timeout handling
- Response routing via correlation ID
- Multiple response aggregation (for broadcasts)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from waooaw.communication.messaging import (
    Message,
    MessageBus,
    MessageType,
    MessagePriority,
)


class ResponseStatus(str, Enum):
    """Response status codes."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"


class TimeoutError(Exception):
    """Raised when request times out."""
    pass


@dataclass
class Request:
    """Request message with response tracking."""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    method: str = ""  # e.g., "get_agent_status", "execute_task"
    params: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_message(self) -> Message:
        """Convert request to message."""
        return Message(
            message_id=self.request_id,
            from_agent=self.from_agent,
            to_agent=self.to_agent,
            message_type=MessageType.QUERY,
            priority=MessagePriority.NORMAL,
            payload={
                "method": self.method,
                "params": self.params,
            },
            correlation_id=self.request_id,
            reply_to=self.from_agent,
            ttl_seconds=self.timeout_seconds,
        )


@dataclass
class Response:
    """Response message with status."""
    
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""  # Correlation ID
    from_agent: str = ""
    to_agent: str = ""
    status: ResponseStatus = ResponseStatus.SUCCESS
    result: Any = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_message(self) -> Message:
        """Convert response to message."""
        return Message(
            message_id=self.response_id,
            from_agent=self.from_agent,
            to_agent=self.to_agent,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,  # Responses get priority
            payload={
                "status": self.status.value,
                "result": self.result,
                "error": self.error,
            },
            correlation_id=self.request_id,
            ttl_seconds=60,
        )
    
    @staticmethod
    def from_message(message: Message) -> "Response":
        """Create response from message."""
        return Response(
            response_id=message.message_id,
            request_id=message.correlation_id or "",
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            status=ResponseStatus(message.payload["status"]),
            result=message.payload.get("result"),
            error=message.payload.get("error"),
            timestamp=message.timestamp,
        )
    
    @staticmethod
    def success(request_id: str, from_agent: str, to_agent: str, result: Any) -> "Response":
        """Create success response."""
        return Response(
            request_id=request_id,
            from_agent=from_agent,
            to_agent=to_agent,
            status=ResponseStatus.SUCCESS,
            result=result,
        )
    
    @staticmethod
    def error(request_id: str, from_agent: str, to_agent: str, error: str) -> "Response":
        """Create error response."""
        return Response(
            request_id=request_id,
            from_agent=from_agent,
            to_agent=to_agent,
            status=ResponseStatus.ERROR,
            error=error,
        )


class RequestResponseHandler:
    """
    Request-response pattern handler.
    
    Enables synchronous-style communication over async message bus:
    - Send request, wait for response
    - Timeout handling
    - Response routing via correlation ID
    """
    
    def __init__(self, message_bus: MessageBus):
        """
        Initialize handler.
        
        Args:
            message_bus: MessageBus instance
        """
        self.message_bus = message_bus
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        # Register handler for response messages
        message_bus.register_handler(MessageType.RESPONSE, self._handle_response)
        message_bus.register_handler(MessageType.QUERY, self._handle_query)
        
        self.query_handlers: Dict[str, Any] = {}  # method -> handler
    
    def register_query_handler(self, method: str, handler: Any):
        """
        Register handler for query method.
        
        Args:
            method: Method name (e.g., "get_status")
            handler: Async function to handle query
        """
        self.query_handlers[method] = handler
    
    async def send_request(
        self,
        to_agent: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Response:
        """
        Send request and wait for response.
        
        Args:
            to_agent: Agent to send request to
            method: Method to call on remote agent
            params: Method parameters
            timeout: Timeout in seconds
            
        Returns:
            Response from remote agent
            
        Raises:
            TimeoutError: If response not received within timeout
        """
        if not self.message_bus.agent_id:
            raise RuntimeError("MessageBus not started")
        
        request = Request(
            from_agent=self.message_bus.agent_id,
            to_agent=to_agent,
            method=method,
            params=params or {},
            timeout_seconds=timeout,
        )
        
        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self.pending_requests[request.request_id] = future
        
        # Send request message
        await self.message_bus.send_message(
            to_agent=to_agent,
            message_type=MessageType.QUERY,
            payload={
                "method": method,
                "params": params or {},
            },
            priority=MessagePriority.NORMAL,
            ttl_seconds=timeout,
            correlation_id=request.request_id,
            reply_to=self.message_bus.agent_id,
        )
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            # Clean up pending request
            self.pending_requests.pop(request.request_id, None)
            raise TimeoutError(f"Request {request.request_id} timed out after {timeout}s")
        finally:
            # Clean up
            self.pending_requests.pop(request.request_id, None)
    
    async def send_response(
        self,
        request_message: Message,
        status: ResponseStatus,
        result: Any = None,
        error: Optional[str] = None,
    ):
        """
        Send response to request.
        
        Args:
            request_message: Original request message
            status: Response status
            result: Result data
            error: Error message if status is ERROR
        """
        if not request_message.reply_to:
            raise ValueError("Request has no reply_to address")
        
        response = Response(
            request_id=request_message.correlation_id or request_message.message_id,
            from_agent=self.message_bus.agent_id or "",
            to_agent=request_message.reply_to,
            status=status,
            result=result,
            error=error,
        )
        
        await self.message_bus.send_message(
            to_agent=request_message.reply_to,
            message_type=MessageType.RESPONSE,
            payload={
                "status": status.value,
                "result": result,
                "error": error,
            },
            priority=MessagePriority.HIGH,
            correlation_id=request_message.correlation_id or request_message.message_id,
        )
    
    async def broadcast_request(
        self,
        to_agents: List[str],
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> List[Response]:
        """
        Send request to multiple agents and collect responses.
        
        Args:
            to_agents: List of agent IDs
            method: Method to call
            params: Method parameters
            timeout: Timeout in seconds
            
        Returns:
            List of responses from all agents
        """
        # Send requests concurrently
        tasks = [
            self.send_request(agent, method, params, timeout)
            for agent in to_agents
        ]
        
        # Gather responses (some may timeout)
        responses: List[Response] = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Response):
                responses.append(result)
            elif isinstance(result, TimeoutError):
                # Create timeout response
                responses.append(Response(
                    status=ResponseStatus.TIMEOUT,
                    error=str(result),
                ))
        
        return responses
    
    async def _handle_response(self, message: Message):
        """Handle incoming response message."""
        if not message.correlation_id:
            return
        
        future = self.pending_requests.get(message.correlation_id)
        if not future or future.done():
            return
        
        # Create response object
        response = Response.from_message(message)
        
        # Complete future
        future.set_result(response)
    
    async def _handle_query(self, message: Message):
        """Handle incoming query message."""
        method = message.payload.get("method")
        params = message.payload.get("params", {})
        
        handler = self.query_handlers.get(method)
        
        if not handler:
            # Unknown method
            await self.send_response(
                message,
                ResponseStatus.NOT_FOUND,
                error=f"Unknown method: {method}",
            )
            return
        
        try:
            # Call handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**params)
            else:
                result = handler(**params)
            
            # Send success response
            await self.send_response(
                message,
                ResponseStatus.SUCCESS,
                result=result,
            )
            
        except Exception as e:
            # Send error response
            await self.send_response(
                message,
                ResponseStatus.ERROR,
                error=str(e),
            )
