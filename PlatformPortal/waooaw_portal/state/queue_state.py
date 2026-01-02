"""
Queue State Management

Real-time queue monitoring with DLQ management.
"""

import reflex as rx
from typing import List, Optional, Dict
from datetime import datetime
import httpx
import os


# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CODESPACE_NAME = os.getenv("CODESPACE_NAME", "")

if CODESPACE_NAME:
    BACKEND_URL = f"https://{CODESPACE_NAME}-8000.app.github.dev"


class QueueMetrics(rx.Base):
    """Queue metrics model"""
    
    queue_name: str
    messages_pending: int
    throughput_per_sec: float
    consumer_lag: int
    error_rate: float
    oldest_message_age_sec: int
    status: str  # healthy, degraded, critical


class DLQMessage(rx.Base):
    """Dead letter queue message model"""
    
    message_id: str
    queue_name: str
    payload: str
    error_message: str
    retry_count: int
    created_at: str
    last_retry_at: Optional[str] = None


class QueueState(rx.State):
    """
    Queue monitoring state.
    
    Features:
    - Real-time queue metrics
    - DLQ message management
    - Retry failed messages
    - WebSocket updates
    """
    
    # Queues
    queues: List[QueueMetrics] = []
    
    # DLQ messages
    dlq_messages: List[DLQMessage] = []
    
    # Selected queue for details
    selected_queue: Optional[str] = None
    
    # UI state
    is_loading: bool = False
    show_dlq_panel: bool = False
    using_mock_data: bool = False  # Track if we're using fallback mock data
    
    def load_queues(self):
        """Load queue metrics from backend API"""
        self.is_loading = True
        
        try:
            # Call backend API
            response = httpx.get(f"{BACKEND_URL}/api/queues", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                self.queues = [QueueMetrics(**q) for q in data]
                
                # Check if backend is returning mock or real data
                data_source = response.headers.get("X-Data-Source", "mock")
                self.using_mock_data = (data_source == "mock")
            else:
                # Fallback to mock data on error
                print(f"Backend API returned status {response.status_code}, using mock data")
                self._load_mock_queues()
                self.using_mock_data = True  # Using fallback mock data
        except Exception as e:
            # Fallback to mock data on connection error
            print(f"Error loading queues: {e}, using mock data")
            self._load_mock_queues()
            self.using_mock_data = True  # Using fallback mock data
        
        self.is_loading = False
    
    def _load_mock_queues(self):
        """Fallback mock data"""
        self.queues = [
            QueueMetrics(
                queue_name="agent-tasks",
                messages_pending=1523,
                throughput_per_sec=45.2,
                consumer_lag=234,
                error_rate=0.8,
                oldest_message_age_sec=120,
                status="degraded",
            ),
            QueueMetrics(
                queue_name="event-bus",
                messages_pending=89,
                throughput_per_sec=156.7,
                consumer_lag=12,
                error_rate=0.1,
                oldest_message_age_sec=5,
                status="healthy",
            ),
            QueueMetrics(
                queue_name="notifications",
                messages_pending=2341,
                throughput_per_sec=23.1,
                consumer_lag=890,
                error_rate=2.3,
                oldest_message_age_sec=450,
                status="critical",
            ),
            QueueMetrics(
                queue_name="webhooks",
                messages_pending=45,
                throughput_per_sec=12.5,
                consumer_lag=5,
                error_rate=0.3,
                oldest_message_age_sec=15,
                status="healthy",
            ),
        ]
    
    def load_dlq(self):
        """Load DLQ messages from backend API"""
        try:
            response = httpx.get(f"{BACKEND_URL}/api/queues/dlq", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                self.dlq_messages = [DLQMessage(**m) for m in data]
            else:
                self._load_mock_dlq()
        except Exception as e:
            print(f"Error loading DLQ: {e}")
            self._load_mock_dlq()
        
        self.show_dlq_panel = True
    
    def _load_mock_dlq(self):
        """Fallback mock DLQ data"""
        self.dlq_messages = [
            DLQMessage(
                message_id="dlq-1",
                queue_name="agent-tasks",
                payload='{"task_id": "task-123", "action": "process"}',
                error_message="Connection timeout after 30s",
                retry_count=3,
                created_at="15 minutes ago",
            ),
            DLQMessage(
                message_id="dlq-2",
                queue_name="notifications",
                payload='{"user_id": "user-456", "type": "email"}',
                error_message="SMTP server unavailable (500)",
                retry_count=5,
                created_at="1 hour ago",
                last_retry_at="30 minutes ago",
            ),
        ]
    
    def retry_message(self, message_id: str):
        """Retry a failed message via backend API"""
        try:
            response = httpx.post(
                f"{BACKEND_URL}/api/queues/dlq/{message_id}/retry",
                timeout=5.0
            )
            
            if response.status_code == 200:
                # Update local state
                for msg in self.dlq_messages:
                    if msg.message_id == message_id:
                        msg.retry_count += 1
                        msg.last_retry_at = "just now"
                        break
        except Exception as e:
            print(f"Error retrying message: {e}")
    
    def delete_message(self, message_id: str):
        """Delete a DLQ message via backend API"""
        try:
            response = httpx.delete(
                f"{BACKEND_URL}/api/queues/dlq/{message_id}",
                timeout=5.0
            )
            
            if response.status_code == 200:
                # Remove from local state
                self.dlq_messages = [m for m in self.dlq_messages if m.message_id != message_id]
        except Exception as e:
            print(f"Error deleting message: {e}")
    
    def select_queue(self, queue_name: str):
        """Select a queue for details"""
        self.selected_queue = queue_name
    
    def close_dlq_panel(self):
        """Close DLQ panel"""
        self.show_dlq_panel = False
    
    @rx.var
    def queue_count(self) -> int:
        """Total queue count"""
        return len(self.queues)
    
    @rx.var
    def healthy_count(self) -> int:
        """Healthy queue count"""
        return len([q for q in self.queues if q.status == "healthy"])
    
    @rx.var
    def degraded_count(self) -> int:
        """Degraded queue count"""
        return len([q for q in self.queues if q.status == "degraded"])
    
    @rx.var
    def critical_count(self) -> int:
        """Critical queue count"""
        return len([q for q in self.queues if q.status == "critical"])
    
    @rx.var
    def dlq_count(self) -> int:
        """DLQ message count"""
        return len(self.dlq_messages)
