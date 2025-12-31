"""
Tests for Prompt Version Manager
"""

import pytest
from datetime import datetime, timedelta
from app.services.testing.version_manager import (
    PromptVersion,
    PromptVersionManager,
    VersionStatus
)


class TestPromptVersion:
    """Test PromptVersion dataclass"""
    
    def test_create_version(self):
        """Test creating a prompt version"""
        version = PromptVersion(
            id="",
            prompt_name="test_prompt",
            version="v1.0",
            content="This is a test prompt"
        )
        
        assert version.prompt_name == "test_prompt"
        assert version.version == "v1.0"
        assert version.content == "This is a test prompt"
        assert version.status == VersionStatus.DRAFT
        assert version.id  # Should be auto-generated
    
    def test_version_id_generation(self):
        """Test version ID is unique based on content"""
        v1 = PromptVersion(
            id="",
            prompt_name="test",
            version="v1.0",
            content="Content A"
        )
        v2 = PromptVersion(
            id="",
            prompt_name="test",
            version="v1.0",
            content="Content B"
        )
        
        assert v1.id != v2.id  # Different content = different ID
    
    def test_version_with_metrics(self):
        """Test version with performance metrics"""
        version = PromptVersion(
            id="",
            prompt_name="test",
            version="v1.0",
            content="Test",
            success_rate=0.85,
            avg_rating=4.5,
            avg_duration_ms=150,
            total_uses=100
        )
        
        assert version.success_rate == 0.85
        assert version.avg_rating == 4.5
        assert version.avg_duration_ms == 150
        assert version.total_uses == 100
    
    def test_version_to_dict(self):
        """Test converting version to dict"""
        version = PromptVersion(
            id="test_id",
            prompt_name="test",
            version="v1.0",
            content="Test content"
        )
        
        data = version.to_dict()
        
        assert data["id"] == "test_id"
        assert data["prompt_name"] == "test"
        assert data["version"] == "v1.0"
        assert data["content"] == "Test content"
        assert data["status"] == "draft"


class TestPromptVersionManager:
    """Test PromptVersionManager"""
    
    @pytest.fixture
    def manager(self):
        """Create version manager for testing"""
        return PromptVersionManager()
    
    def test_create_version(self, manager):
        """Test creating a new version"""
        version = manager.create_version(
            prompt_name="content_creation",
            content="Create engaging content about {topic}",
            commit_message="Initial version"
        )
        
        assert version.prompt_name == "content_creation"
        assert version.version == "v1.0"
        assert version.status == VersionStatus.DRAFT
        assert version.commit_message == "Initial version"
    
    def test_auto_increment_version(self, manager):
        """Test version auto-increment"""
        v1 = manager.create_version(
            prompt_name="test",
            content="Version 1"
        )
        v2 = manager.create_version(
            prompt_name="test",
            content="Version 2"
        )
        v3 = manager.create_version(
            prompt_name="test",
            content="Version 3"
        )
        
        assert v1.version == "v1.0"
        assert v2.version == "v1.1"
        assert v3.version == "v1.2"
    
    def test_get_version(self, manager):
        """Test retrieving version by ID"""
        v1 = manager.create_version(
            prompt_name="test",
            content="Test"
        )
        
        retrieved = manager.get_version(v1.id)
        
        assert retrieved is not None
        assert retrieved.id == v1.id
        assert retrieved.content == "Test"
    
    def test_list_versions(self, manager):
        """Test listing all versions"""
        manager.create_version(prompt_name="prompt1", content="A")
        manager.create_version(prompt_name="prompt1", content="B")
        manager.create_version(prompt_name="prompt2", content="C")
        
        all_versions = manager.list_versions()
        assert len(all_versions) == 3
        
        prompt1_versions = manager.list_versions(prompt_name="prompt1")
        assert len(prompt1_versions) == 2
    
    def test_list_versions_by_status(self, manager):
        """Test filtering versions by status"""
        v1 = manager.create_version(prompt_name="test", content="A")
        v2 = manager.create_version(prompt_name="test", content="B")
        
        v1.status = VersionStatus.ACTIVE
        v2.status = VersionStatus.DRAFT
        
        active = manager.list_versions(status=VersionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].id == v1.id
        
        draft = manager.list_versions(status=VersionStatus.DRAFT)
        assert len(draft) == 1
        assert draft[0].id == v2.id
    
    def test_get_active_version(self, manager):
        """Test getting active version"""
        v1 = manager.create_version(prompt_name="test", content="Old")
        v2 = manager.create_version(prompt_name="test", content="New")
        
        # No active version yet
        assert manager.get_active_version("test") is None
        
        # Activate v2
        manager.activate_version(v2.id)
        
        active = manager.get_active_version("test")
        assert active is not None
        assert active.id == v2.id
    
    def test_activate_version(self, manager):
        """Test activating a version"""
        v1 = manager.create_version(prompt_name="test", content="V1")
        v2 = manager.create_version(prompt_name="test", content="V2")
        
        # Activate v1
        manager.activate_version(v1.id)
        assert v1.status == VersionStatus.ACTIVE
        
        # Activate v2 (should deactivate v1)
        manager.activate_version(v2.id)
        assert v2.status == VersionStatus.ACTIVE
        assert v1.status == VersionStatus.ARCHIVED
    
    def test_rollback(self, manager):
        """Test rolling back to previous version"""
        v1 = manager.create_version(prompt_name="test", content="V1")
        v2 = manager.create_version(
            prompt_name="test",
            content="V2",
            parent_version=v1.id
        )
        
        # Activate v2
        manager.activate_version(v2.id)
        
        # Rollback to v1
        previous = manager.rollback("test")
        
        assert previous.id == v1.id
        assert previous.status == VersionStatus.ACTIVE
        assert v2.status == VersionStatus.ARCHIVED
    
    def test_rollback_no_parent(self, manager):
        """Test rollback when no parent exists"""
        v1 = manager.create_version(prompt_name="test", content="V1")
        manager.activate_version(v1.id)
        
        # Try to rollback (should fail - no parent)
        result = manager.rollback("test")
        assert result is None
    
    def test_compare_versions(self, manager):
        """Test comparing two versions"""
        v1 = manager.create_version(prompt_name="test", content="Short")
        v2 = manager.create_version(prompt_name="test", content="Much longer content")
        
        # Add metrics
        v1.success_rate = 0.80
        v1.avg_rating = 4.0
        v2.success_rate = 0.85
        v2.avg_rating = 4.5
        
        comparison = manager.compare_versions(v1.id, v2.id)
        
        assert comparison["version1"]["success_rate"] == 0.80
        assert comparison["version2"]["success_rate"] == 0.85
        assert abs(comparison["performance_delta"]["success_rate"] - 0.05) < 0.001  # Float precision
        assert comparison["performance_delta"]["avg_rating"] == 0.5
        assert comparison["content_changed"] is True
    
    def test_tag_version(self, manager):
        """Test tagging versions"""
        v1 = manager.create_version(prompt_name="test", content="Stable")
        v2 = manager.create_version(prompt_name="test", content="Experimental")
        
        manager.tag_version(v1.id, "stable")
        manager.tag_version(v2.id, "experimental")
        
        stable = manager.get_tagged_version("stable")
        experimental = manager.get_tagged_version("experimental")
        
        assert stable.id == v1.id
        assert experimental.id == v2.id
    
    def test_update_metrics(self, manager):
        """Test updating version metrics"""
        version = manager.create_version(prompt_name="test", content="Test")
        
        manager.update_metrics(
            version_id=version.id,
            success_rate=0.90,
            avg_rating=4.8,
            avg_duration_ms=120,
            increment_uses=True
        )
        
        assert version.success_rate == 0.90
        assert version.avg_rating == 4.8
        assert version.avg_duration_ms == 120
        assert version.total_uses == 1
        
        # Increment uses again
        manager.update_metrics(version_id=version.id, increment_uses=True)
        assert version.total_uses == 2
    
    def test_get_history(self, manager):
        """Test getting version history"""
        v1 = manager.create_version(prompt_name="test", content="V1")
        v2 = manager.create_version(prompt_name="test", content="V2")
        v3 = manager.create_version(prompt_name="test", content="V3")
        
        history = manager.get_history("test")
        
        assert len(history) == 3
        assert history[0].id == v1.id  # Oldest first
        assert history[1].id == v2.id
        assert history[2].id == v3.id
    
    def test_delete_version(self, manager):
        """Test deleting a version"""
        v1 = manager.create_version(prompt_name="test", content="V1")
        v2 = manager.create_version(prompt_name="test", content="V2")
        
        # Can delete draft version
        assert manager.delete_version(v1.id) is True
        assert manager.get_version(v1.id) is None
        
        # Cannot delete active version
        manager.activate_version(v2.id)
        assert manager.delete_version(v2.id) is False
        assert manager.get_version(v2.id) is not None
