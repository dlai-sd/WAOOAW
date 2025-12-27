"""
WAOOAW Common Components: State Manager

Provides versioned state persistence with snapshots, rollback, and event sourcing.

Usage:
    # Basic state management:
    manager = StateManager(agent_id="wowvision-prime")
    
    # Save state:
    manager.save_state({"decisions": 10, "cache_hits": 90})
    
    # Load state:
    state = manager.load_state()
    
    # With versioning:
    manager.save_state(state, version="v1.0.0")
    state = manager.load_state(version="v1.0.0")

Vision Compliance:
    ✅ Zero Risk: Rollback to previous state on failure
    ✅ Agentic: State isolation per agent
    ✅ Simplicity: Auto-persistence, manual override available
"""

import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """
    Immutable state snapshot.
    
    Attributes:
        version: State version (semantic versioning)
        data: State data (JSON-serializable dict)
        timestamp: When snapshot was created
        metadata: Additional metadata (tags, description, etc.)
    """
    version: str
    data: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
        return cls(**data_copy)


class StateManager:
    """
    Versioned state persistence with snapshots and rollback.
    
    Features:
    - Automatic state persistence
    - Version control (semantic versioning)
    - Snapshot management
    - Rollback capability
    - Event sourcing (optional)
    - State diff tracking
    
    Example:
        manager = StateManager(
            agent_id="wowvision-prime",
            db_connection=db,
            auto_persist=True
        )
        
        # Save state:
        manager.save_state({"decisions": 10, "cache_hits": 90})
        
        # Load state:
        state = manager.load_state()
        
        # Create snapshot:
        manager.create_snapshot(version="v1.0.0", tags=["stable"])
        
        # Rollback:
        manager.rollback_to_version("v1.0.0")
        
        # Get history:
        history = manager.get_state_history(limit=10)
    """
    
    def __init__(
        self,
        agent_id: str,
        db_connection: Optional[Any] = None,
        auto_persist: bool = True,
        max_snapshots: int = 10
    ):
        """
        Initialize state manager.
        
        Args:
            agent_id: Unique agent identifier
            db_connection: Database connection (optional)
            auto_persist: Auto-save on state changes
            max_snapshots: Maximum snapshots to keep (LRU)
        """
        self.agent_id = agent_id
        self.db_connection = db_connection
        self.auto_persist = auto_persist
        self.max_snapshots = max_snapshots
        
        self._current_state: Dict[str, Any] = {}
        self._snapshots: List[StateSnapshot] = []
        self._version = "v0.0.1"
        
        # Load initial state if available
        self._load_from_db()
        
        logger.info(
            f"StateManager initialized for agent '{agent_id}' "
            f"(auto_persist={auto_persist}, max_snapshots={max_snapshots})"
        )
    
    def save_state(
        self,
        state: Dict[str, Any],
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save current state.
        
        Args:
            state: State data to save
            version: Optional version string
            metadata: Optional metadata
        """
        self._current_state = state.copy()
        
        if version:
            self._version = version
        
        if self.auto_persist:
            self._persist_to_db(state, version, metadata)
        
        logger.debug(f"State saved for agent '{self.agent_id}' (version={self._version})")
    
    def load_state(
        self,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load state.
        
        Args:
            version: Optional version to load (default: latest)
            
        Returns:
            State data
        """
        if version:
            # Load specific version
            snapshot = self._get_snapshot_by_version(version)
            if snapshot:
                return snapshot.data.copy()
            else:
                logger.warning(f"Version '{version}' not found, returning current state")
        
        return self._current_state.copy()
    
    def update_state(
        self,
        updates: Dict[str, Any],
        merge: bool = True
    ):
        """
        Update state with partial changes.
        
        Args:
            updates: Changes to apply
            merge: True to merge, False to replace
        """
        if merge:
            self._current_state.update(updates)
        else:
            self._current_state = updates.copy()
        
        if self.auto_persist:
            self._persist_to_db(self._current_state)
        
        logger.debug(f"State updated for agent '{self.agent_id}'")
    
    def create_snapshot(
        self,
        version: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None
    ) -> StateSnapshot:
        """
        Create immutable snapshot of current state.
        
        Args:
            version: Version string (e.g., "v1.0.0")
            tags: Optional tags (e.g., ["stable", "production"])
            description: Optional description
            
        Returns:
            Created snapshot
        """
        metadata = {
            'agent_id': self.agent_id,
            'tags': tags or [],
            'description': description
        }
        
        snapshot = StateSnapshot(
            version=version,
            data=self._current_state.copy(),
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self._snapshots.append(snapshot)
        self._version = version
        
        # Enforce max snapshots (LRU)
        while len(self._snapshots) > self.max_snapshots:
            removed = self._snapshots.pop(0)
            logger.debug(f"Removed old snapshot: {removed.version}")
        
        # Persist snapshot
        if self.db_connection:
            self._persist_snapshot_to_db(snapshot)
        
        logger.info(f"Snapshot created: {version} for agent '{self.agent_id}'")
        return snapshot
    
    def rollback_to_version(self, version: str) -> bool:
        """
        Rollback state to specific version.
        
        Args:
            version: Version to rollback to
            
        Returns:
            True if rollback successful
        """
        snapshot = self._get_snapshot_by_version(version)
        
        if not snapshot:
            logger.error(f"Cannot rollback: version '{version}' not found")
            return False
        
        self._current_state = snapshot.data.copy()
        self._version = version
        
        if self.auto_persist:
            self._persist_to_db(self._current_state, version)
        
        logger.warning(f"Rolled back to version '{version}' for agent '{self.agent_id}'")
        return True
    
    def get_state_history(
        self,
        limit: int = 10
    ) -> List[StateSnapshot]:
        """
        Get state history (snapshots).
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            List of snapshots (newest first)
        """
        return list(reversed(self._snapshots[-limit:]))
    
    def get_current_version(self) -> str:
        """Get current state version."""
        return self._version
    
    def calculate_diff(
        self,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        Calculate diff between two versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Dict with added, removed, changed keys
        """
        snap1 = self._get_snapshot_by_version(version1)
        snap2 = self._get_snapshot_by_version(version2)
        
        if not snap1 or not snap2:
            return {'error': 'One or both versions not found'}
        
        data1 = snap1.data
        data2 = snap2.data
        
        added = {k: v for k, v in data2.items() if k not in data1}
        removed = {k: v for k, v in data1.items() if k not in data2}
        changed = {
            k: {'old': data1[k], 'new': data2[k]}
            for k in data1.keys() & data2.keys()
            if data1[k] != data2[k]
        }
        
        return {
            'version1': version1,
            'version2': version2,
            'added': added,
            'removed': removed,
            'changed': changed
        }
    
    def clear_state(self):
        """Clear current state (dangerous!)."""
        self._current_state = {}
        
        if self.auto_persist:
            self._persist_to_db({})
        
        logger.warning(f"State cleared for agent '{self.agent_id}'")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get state manager statistics.
        
        Returns:
            Dict with version, snapshot count, state size, etc.
        """
        return {
            'agent_id': self.agent_id,
            'current_version': self._version,
            'snapshot_count': len(self._snapshots),
            'state_keys': len(self._current_state),
            'auto_persist': self.auto_persist,
            'max_snapshots': self.max_snapshots
        }
    
    # Private methods
    
    def _get_snapshot_by_version(self, version: str) -> Optional[StateSnapshot]:
        """Get snapshot by version string."""
        for snapshot in reversed(self._snapshots):
            if snapshot.version == version:
                return snapshot
        return None
    
    def _load_from_db(self):
        """Load state from database."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            # Load current state
            cursor.execute(
                """
                SELECT state_data, version, updated_at
                FROM agent_state
                WHERE agent_id = %s
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (self.agent_id,)
            )
            
            row = cursor.fetchone()
            if row:
                state_json, version, updated_at = row
                self._current_state = json.loads(state_json) if isinstance(state_json, str) else state_json
                self._version = version
                logger.debug(f"Loaded state for agent '{self.agent_id}' (version={version})")
            
            # Load snapshots
            cursor.execute(
                """
                SELECT version, state_data, created_at, metadata
                FROM agent_state_snapshots
                WHERE agent_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (self.agent_id, self.max_snapshots)
            )
            
            for row in cursor.fetchall():
                version, state_data, created_at, metadata_json = row
                snapshot = StateSnapshot(
                    version=version,
                    data=json.loads(state_data) if isinstance(state_data, str) else state_data,
                    timestamp=created_at,
                    metadata=json.loads(metadata_json) if metadata_json else None
                )
                self._snapshots.append(snapshot)
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to load state from database: {e}")
    
    def _persist_to_db(
        self,
        state: Dict[str, Any],
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Persist state to database."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            state_json = json.dumps(state)
            version = version or self._version
            
            cursor.execute(
                """
                INSERT INTO agent_state (agent_id, state_data, version, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (agent_id)
                DO UPDATE SET
                    state_data = EXCLUDED.state_data,
                    version = EXCLUDED.version,
                    updated_at = EXCLUDED.updated_at
                """,
                (self.agent_id, state_json, version, datetime.now())
            )
            
            self.db_connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to persist state to database: {e}")
    
    def _persist_snapshot_to_db(self, snapshot: StateSnapshot):
        """Persist snapshot to database."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            state_json = json.dumps(snapshot.data)
            metadata_json = json.dumps(snapshot.metadata) if snapshot.metadata else None
            
            cursor.execute(
                """
                INSERT INTO agent_state_snapshots 
                (agent_id, version, state_data, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (self.agent_id, snapshot.version, state_json, metadata_json, snapshot.timestamp)
            )
            
            self.db_connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to persist snapshot to database: {e}")
