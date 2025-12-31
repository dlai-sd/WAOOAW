"""
Prompt Version Manager

Git-like version control for prompts with rollback capabilities.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json


class VersionStatus(str, Enum):
    """Status of prompt version"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class PromptVersion:
    """Single version of a prompt"""
    id: str  # Hash of content
    prompt_name: str  # e.g., "content_creation_marketing"
    version: str  # e.g., "v1.0", "v1.1", "v2.0"
    content: str  # Full prompt text
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: VersionStatus = VersionStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    parent_version: Optional[str] = None  # Previous version
    commit_message: Optional[str] = None
    
    # Performance metrics (filled after testing)
    success_rate: Optional[float] = None
    avg_rating: Optional[float] = None
    avg_duration_ms: Optional[int] = None
    total_uses: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID based on content hash"""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        return f"{self.prompt_name}:{self.version}:{content_hash[:8]}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "prompt_name": self.prompt_name,
            "version": self.version,
            "content": self.content,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_version": self.parent_version,
            "commit_message": self.commit_message,
            "success_rate": self.success_rate,
            "avg_rating": self.avg_rating,
            "avg_duration_ms": self.avg_duration_ms,
            "total_uses": self.total_uses
        }


class PromptVersionManager:
    """
    Manages prompt versions with git-like operations.
    
    Features:
    - Create new versions
    - List version history
    - Rollback to previous versions
    - Compare versions (diff)
    - Tag versions (e.g., "stable", "experimental")
    """
    
    def __init__(self, storage: Optional[Dict] = None):
        """
        Initialize version manager.
        
        Args:
            storage: Storage backend (dict for testing, database in prod)
        """
        self.storage = storage if storage is not None else {}
        self._tags: Dict[str, str] = {}  # tag_name -> version_id
    
    def create_version(
        self,
        prompt_name: str,
        content: str,
        version: Optional[str] = None,
        parent_version: Optional[str] = None,
        commit_message: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> PromptVersion:
        """
        Create new prompt version.
        
        Args:
            prompt_name: Name of prompt
            content: Prompt content
            version: Version string (auto-incremented if None)
            parent_version: Previous version ID
            commit_message: Commit message
            created_by: User who created version
            metadata: Additional metadata
            
        Returns:
            Created PromptVersion
        """
        # Auto-increment version if not provided
        if version is None:
            version = self._next_version(prompt_name)
        
        prompt_version = PromptVersion(
            id="",  # Will be generated
            prompt_name=prompt_name,
            version=version,
            content=content,
            metadata=metadata or {},
            parent_version=parent_version,
            commit_message=commit_message,
            created_by=created_by
        )
        
        # Store version
        self.storage[prompt_version.id] = prompt_version
        
        return prompt_version
    
    def get_version(self, version_id: str) -> Optional[PromptVersion]:
        """Get version by ID"""
        return self.storage.get(version_id)
    
    def list_versions(
        self,
        prompt_name: Optional[str] = None,
        status: Optional[VersionStatus] = None
    ) -> List[PromptVersion]:
        """
        List all versions with optional filters.
        
        Args:
            prompt_name: Filter by prompt name
            status: Filter by status
            
        Returns:
            List of versions, sorted by creation date (newest first)
        """
        versions = list(self.storage.values())
        
        # Apply filters
        if prompt_name:
            versions = [v for v in versions if v.prompt_name == prompt_name]
        if status:
            versions = [v for v in versions if v.status == status]
        
        # Sort by creation date (newest first)
        versions.sort(key=lambda v: v.created_at, reverse=True)
        
        return versions
    
    def get_active_version(self, prompt_name: str) -> Optional[PromptVersion]:
        """Get currently active version of prompt"""
        active_versions = self.list_versions(
            prompt_name=prompt_name,
            status=VersionStatus.ACTIVE
        )
        return active_versions[0] if active_versions else None
    
    def activate_version(self, version_id: str) -> bool:
        """
        Activate a version (make it production).
        Deactivates other versions of same prompt.
        
        Args:
            version_id: Version to activate
            
        Returns:
            True if successful
        """
        version = self.get_version(version_id)
        if not version:
            return False
        
        # Deactivate other versions of same prompt
        for v in self.list_versions(prompt_name=version.prompt_name):
            if v.status == VersionStatus.ACTIVE:
                v.status = VersionStatus.ARCHIVED
        
        # Activate this version
        version.status = VersionStatus.ACTIVE
        
        return True
    
    def rollback(self, prompt_name: str) -> Optional[PromptVersion]:
        """
        Rollback to previous active version.
        
        Args:
            prompt_name: Name of prompt to rollback
            
        Returns:
            Previous version (now active), or None if no previous version
        """
        # Get current active version
        current = self.get_active_version(prompt_name)
        if not current or not current.parent_version:
            return None
        
        # Get parent version
        parent = self.get_version(current.parent_version)
        if not parent:
            return None
        
        # Activate parent
        self.activate_version(parent.id)
        
        return parent
    
    def compare_versions(
        self,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions.
        
        Args:
            version_id1: First version
            version_id2: Second version
            
        Returns:
            Comparison dict with differences
        """
        v1 = self.get_version(version_id1)
        v2 = self.get_version(version_id2)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        # Simple comparison
        return {
            "version1": {
                "id": v1.id,
                "version": v1.version,
                "content_length": len(v1.content),
                "success_rate": v1.success_rate,
                "avg_rating": v1.avg_rating
            },
            "version2": {
                "id": v2.id,
                "version": v2.version,
                "content_length": len(v2.content),
                "success_rate": v2.success_rate,
                "avg_rating": v2.avg_rating
            },
            "content_changed": v1.content != v2.content,
            "performance_delta": {
                "success_rate": (v2.success_rate or 0) - (v1.success_rate or 0),
                "avg_rating": (v2.avg_rating or 0) - (v1.avg_rating or 0)
            }
        }
    
    def tag_version(self, version_id: str, tag: str):
        """Tag a version (e.g., 'stable', 'best')"""
        self._tags[tag] = version_id
    
    def get_tagged_version(self, tag: str) -> Optional[PromptVersion]:
        """Get version by tag"""
        version_id = self._tags.get(tag)
        return self.get_version(version_id) if version_id else None
    
    def update_metrics(
        self,
        version_id: str,
        success_rate: Optional[float] = None,
        avg_rating: Optional[float] = None,
        avg_duration_ms: Optional[int] = None,
        increment_uses: bool = False
    ):
        """Update performance metrics for version"""
        version = self.get_version(version_id)
        if not version:
            return
        
        if success_rate is not None:
            version.success_rate = success_rate
        if avg_rating is not None:
            version.avg_rating = avg_rating
        if avg_duration_ms is not None:
            version.avg_duration_ms = avg_duration_ms
        if increment_uses:
            version.total_uses += 1
    
    def _next_version(self, prompt_name: str) -> str:
        """Auto-increment version number"""
        versions = self.list_versions(prompt_name=prompt_name)
        
        if not versions:
            return "v1.0"
        
        # Get latest version
        latest = versions[0]
        
        # Parse version (assume format: v1.0, v1.1, v2.0)
        try:
            parts = latest.version.strip('v').split('.')
            major, minor = int(parts[0]), int(parts[1])
            
            # Increment minor version
            return f"v{major}.{minor + 1}"
        except:
            # Fallback if parsing fails
            return f"v{len(versions) + 1}.0"
    
    def get_history(self, prompt_name: str) -> List[PromptVersion]:
        """Get version history for prompt (chronological)"""
        versions = self.list_versions(prompt_name=prompt_name)
        versions.sort(key=lambda v: v.created_at)  # Oldest first
        return versions
    
    def delete_version(self, version_id: str) -> bool:
        """Delete version (only if not active)"""
        version = self.get_version(version_id)
        if not version or version.status == VersionStatus.ACTIVE:
            return False
        
        del self.storage[version_id]
        return True
