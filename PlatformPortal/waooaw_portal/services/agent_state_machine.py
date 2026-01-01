"""
Agent State Machine Service

Manages agent lifecycle state transitions with validation and audit trail.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states"""

    DRAFT = "draft"
    PROVISIONED = "provisioned"
    DEPLOYED = "deployed"
    RUNNING = "running"
    STOPPED = "stopped"
    SUSPENDED = "suspended"
    ERRORED = "errored"
    REVOKED = "revoked"


@dataclass
class StateTransition:
    """Record of a state transition"""

    agent_id: str
    from_state: AgentState
    to_state: AgentState
    triggered_by: str
    timestamp: datetime
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class AgentStateMachine:
    """
    Agent state machine with validation and audit trail.

    State Flow:
    DRAFT → PROVISIONED → DEPLOYED → RUNNING ⇄ STOPPED
                                    ↓         ↓
                                  SUSPENDED   ERRORED
                                    ↓
    ANY → REVOKED (terminal)

    Features:
    - Transition validation
    - Audit trail logging
    - State history tracking
    - Error handling
    """
    
    @staticmethod
    def get_state_enum(state_str: str) -> AgentState:
        """Convert string to AgentState enum"""
        try:
            return AgentState(state_str.lower())
        except ValueError:
            return AgentState.DRAFT

    # Valid state transitions
    TRANSITIONS: Dict[AgentState, List[AgentState]] = {
        AgentState.DRAFT: [AgentState.PROVISIONED, AgentState.REVOKED],
        AgentState.PROVISIONED: [
            AgentState.DEPLOYED,
            AgentState.ERRORED,
            AgentState.REVOKED,
        ],
        AgentState.DEPLOYED: [
            AgentState.RUNNING,
            AgentState.STOPPED,
            AgentState.ERRORED,
            AgentState.REVOKED,
        ],
        AgentState.RUNNING: [
            AgentState.STOPPED,
            AgentState.SUSPENDED,
            AgentState.ERRORED,
            AgentState.REVOKED,
        ],
        AgentState.STOPPED: [
            AgentState.RUNNING,
            AgentState.DEPLOYED,
            AgentState.REVOKED,
        ],
        AgentState.SUSPENDED: [
            AgentState.RUNNING,
            AgentState.STOPPED,
            AgentState.REVOKED,
        ],
        AgentState.ERRORED: [
            AgentState.RUNNING,
            AgentState.STOPPED,
            AgentState.DEPLOYED,
            AgentState.REVOKED,
        ],
        AgentState.REVOKED: [],  # Terminal state
    }

    # State transition actions (what actually happens during transition)
    STATE_ACTIONS = {
        (AgentState.DRAFT, AgentState.PROVISIONED): "allocate_resources",
        (AgentState.PROVISIONED, AgentState.DEPLOYED): "deploy_container",
        (AgentState.DEPLOYED, AgentState.RUNNING): "start_agent",
        (AgentState.RUNNING, AgentState.STOPPED): "stop_agent",
        (AgentState.RUNNING, AgentState.SUSPENDED): "suspend_agent",
        (AgentState.SUSPENDED, AgentState.RUNNING): "resume_agent",
        (AgentState.STOPPED, AgentState.RUNNING): "restart_agent",
    }

    def __init__(self):
        """Initialize state machine"""
        self.transition_history: List[StateTransition] = []

    def can_transition(self, current: AgentState, target: AgentState) -> bool:
        """
        Check if state transition is valid.

        Args:
            current: Current agent state
            target: Target agent state

        Returns:
            True if transition is allowed, False otherwise
        """
        return target in self.TRANSITIONS.get(current, [])

    def transition(
        self,
        agent_id: str,
        current: AgentState,
        target: AgentState,
        triggered_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateTransition:
        """
        Attempt state transition with validation.

        Args:
            agent_id: Agent identifier
            current: Current agent state
            target: Target agent state
            triggered_by: User/system that triggered transition
            metadata: Additional transition metadata

        Returns:
            StateTransition record

        Raises:
            ValueError: If transition is invalid
        """
        # Validate transition
        if not self.can_transition(current, target):
            error_msg = f"Invalid transition: {current.value} → {target.value}"
            logger.error(f"Agent {agent_id}: {error_msg}")

            transition = StateTransition(
                agent_id=agent_id,
                from_state=current,
                to_state=target,
                triggered_by=triggered_by,
                timestamp=datetime.now(),
                metadata=metadata or {},
                success=False,
                error_message=error_msg,
            )
            self.transition_history.append(transition)
            raise ValueError(error_msg)

        # Execute transition action
        action = self.STATE_ACTIONS.get((current, target))
        if action:
            logger.info(f"Agent {agent_id}: Executing {action} for {current.value} → {target.value}")

        # Record successful transition
        transition = StateTransition(
            agent_id=agent_id,
            from_state=current,
            to_state=target,
            triggered_by=triggered_by,
            timestamp=datetime.now(),
            metadata=metadata or {},
            success=True,
        )
        self.transition_history.append(transition)

        logger.info(
            f"Agent {agent_id}: Successfully transitioned {current.value} → {target.value} "
            f"by {triggered_by}"
        )

        return transition

    def get_valid_transitions(self, current: AgentState) -> List[AgentState]:
        """Get list of valid target states from current state"""
        return self.TRANSITIONS.get(current, [])

    def get_transition_history(
        self, agent_id: Optional[str] = None, limit: int = 50
    ) -> List[StateTransition]:
        """
        Get transition history.

        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of transitions to return

        Returns:
            List of state transitions (newest first)
        """
        history = self.transition_history
        if agent_id:
            history = [t for t in history if t.agent_id == agent_id]

        # Sort by timestamp descending
        history.sort(key=lambda t: t.timestamp, reverse=True)
        return history[:limit]

    def get_state_color(self, state: AgentState) -> str:
        """Get color scheme for state badge"""
        colors = {
            AgentState.DRAFT: "gray",
            AgentState.PROVISIONED: "blue",
            AgentState.DEPLOYED: "cyan",
            AgentState.RUNNING: "green",
            AgentState.STOPPED: "gray",
            AgentState.SUSPENDED: "yellow",
            AgentState.ERRORED: "red",
            AgentState.REVOKED: "red",
        }
        return colors.get(state, "gray")

    def get_state_icon(self, state: AgentState) -> str:
        """Get icon for state"""
        icons = {
            AgentState.DRAFT: "file_text",
            AgentState.PROVISIONED: "package",
            AgentState.DEPLOYED: "upload",
            AgentState.RUNNING: "play",
            AgentState.STOPPED: "square",
            AgentState.SUSPENDED: "pause",
            AgentState.ERRORED: "alert_circle",
            AgentState.REVOKED: "x_circle",
        }
        return icons.get(state, "circle")

    def get_state_label(self, state: AgentState) -> str:
        """Get human-readable state label"""
        return state.value.replace("_", " ").title()
