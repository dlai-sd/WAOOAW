"""
Unit Tests for Knowledge Graph - Story 4.4
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.learning.knowledge_graph import (
    KnowledgeGraph,
    NodeType,
    RelationType
)


class TestKnowledgeGraph:
    """Test knowledge graph."""
    
    def test_init(self):
        """Should initialize graph."""
        graph = KnowledgeGraph()
        
        assert len(graph.nodes) == 0
        assert len(graph.relations) == 0
    
    def test_add_node(self):
        """Should add nodes."""
        graph = KnowledgeGraph()
        
        node_id = graph.add_node(
            NodeType.ENTITY,
            "User",
            {"email": "user@example.com"}
        )
        
        assert node_id.startswith("entity_")
        assert len(graph.nodes) == 1
    
    def test_add_relation(self):
        """Should add relationships."""
        graph = KnowledgeGraph()
        
        user_id = graph.add_node(NodeType.ENTITY, "User")
        skill_id = graph.add_node(NodeType.SKILL, "Python")
        
        rel_id = graph.add_relation(
            user_id,
            skill_id,
            RelationType.HAS_A
        )
        
        assert rel_id.startswith("rel_")
        assert len(graph.relations) == 1
    
    def test_get_nodes_by_type(self):
        """Should get nodes by type."""
        graph = KnowledgeGraph()
        
        graph.add_node(NodeType.SKILL, "Python")
        graph.add_node(NodeType.SKILL, "JavaScript")
        graph.add_node(NodeType.ENTITY, "User")
        
        skills = graph.get_nodes_by_type(NodeType.SKILL)
        
        assert len(skills) == 2
    
    def test_get_relations_for_node(self):
        """Should get relations for a node."""
        graph = KnowledgeGraph()
        
        user_id = graph.add_node(NodeType.ENTITY, "User")
        skill1_id = graph.add_node(NodeType.SKILL, "Python")
        skill2_id = graph.add_node(NodeType.SKILL, "JavaScript")
        
        graph.add_relation(user_id, skill1_id, RelationType.HAS_A)
        graph.add_relation(user_id, skill2_id, RelationType.HAS_A)
        
        relations = graph.get_relations_for_node(user_id, "outgoing")
        
        assert len(relations) == 2
    
    def test_find_path(self):
        """Should find shortest path between nodes."""
        graph = KnowledgeGraph()
        
        # Create chain: A -> B -> C
        a_id = graph.add_node(NodeType.ENTITY, "A")
        b_id = graph.add_node(NodeType.ENTITY, "B")
        c_id = graph.add_node(NodeType.ENTITY, "C")
        
        graph.add_relation(a_id, b_id, RelationType.RELATED_TO)
        graph.add_relation(b_id, c_id, RelationType.RELATED_TO)
        
        path = graph.find_path(a_id, c_id)
        
        assert path is not None
        assert len(path) == 3
        assert path == [a_id, b_id, c_id]
    
    def test_find_similar_nodes(self):
        """Should find similar nodes by shared relations."""
        graph = KnowledgeGraph()
        
        # Create shared skills
        user1_id = graph.add_node(NodeType.ENTITY, "User1")
        user2_id = graph.add_node(NodeType.ENTITY, "User2")
        skill1_id = graph.add_node(NodeType.SKILL, "Python")
        skill2_id = graph.add_node(NodeType.SKILL, "JavaScript")
        
        # Both users have Python
        graph.add_relation(user1_id, skill1_id, RelationType.HAS_A)
        graph.add_relation(user2_id, skill1_id, RelationType.HAS_A)
        
        # User1 also has JavaScript
        graph.add_relation(user1_id, skill2_id, RelationType.HAS_A)
        
        similar = graph.find_similar_nodes(user1_id, min_similarity=0.3)
        
        assert len(similar) > 0
        assert similar[0][0] == user2_id
    
    def test_get_subgraph(self):
        """Should extract subgraph."""
        graph = KnowledgeGraph()
        
        center_id = graph.add_node(NodeType.ENTITY, "Center")
        neighbor1_id = graph.add_node(NodeType.ENTITY, "Neighbor1")
        neighbor2_id = graph.add_node(NodeType.ENTITY, "Neighbor2")
        
        graph.add_relation(center_id, neighbor1_id, RelationType.RELATED_TO)
        graph.add_relation(center_id, neighbor2_id, RelationType.RELATED_TO)
        
        subgraph = graph.get_subgraph(center_id, max_depth=1)
        
        assert len(subgraph["nodes"]) == 3
        assert len(subgraph["relations"]) == 2
    
    def test_stats(self):
        """Should report statistics."""
        graph = KnowledgeGraph()
        
        graph.add_node(NodeType.ENTITY, "User")
        graph.add_node(NodeType.SKILL, "Python")
        
        stats = graph.get_stats()
        
        assert stats["total_nodes"] == 2
        assert stats["nodes_by_type"]["entity"] == 1
        assert stats["nodes_by_type"]["skill"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
