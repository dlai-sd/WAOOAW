"""
Tests for Knowledge Graph
"""

import pytest
from app.services.specialization.knowledge_graph import (
    KnowledgeGraph,
    Entity,
    Relationship,
    EntityType,
    RelationshipType,
    DomainOntology,
    GraphQueryEngine
)


class TestEntity:
    """Test Entity dataclass"""
    
    def test_create_entity(self):
        """Test creating an entity"""
        entity = Entity(
            id="campaign1",
            type=EntityType.CAMPAIGN,
            name="Summer Campaign",
            properties={"budget": 10000, "duration": "3 months"}
        )
        
        assert entity.id == "campaign1"
        assert entity.type == EntityType.CAMPAIGN
        assert entity.name == "Summer Campaign"
        assert entity.properties["budget"] == 10000
    
    def test_entity_to_dict(self):
        """Test entity serialization"""
        entity = Entity(
            id="channel1",
            type=EntityType.CHANNEL,
            name="LinkedIn",
            properties={"category": "social"}
        )
        
        data = entity.to_dict()
        
        assert data["id"] == "channel1"
        assert data["type"] == "channel"
        assert data["name"] == "LinkedIn"
        assert data["properties"]["category"] == "social"


class TestRelationship:
    """Test Relationship dataclass"""
    
    def test_create_relationship(self):
        """Test creating a relationship"""
        rel = Relationship(
            id="rel1",
            type=RelationshipType.TARGETS,
            source_id="campaign1",
            target_id="audience1",
            strength=0.8
        )
        
        assert rel.id == "rel1"
        assert rel.type == RelationshipType.TARGETS
        assert rel.source_id == "campaign1"
        assert rel.target_id == "audience1"
        assert rel.strength == 0.8
    
    def test_relationship_to_dict(self):
        """Test relationship serialization"""
        rel = Relationship(
            id="rel1",
            type=RelationshipType.USES_CHANNEL,
            source_id="campaign1",
            target_id="linkedin",
            properties={"priority": "high"}
        )
        
        data = rel.to_dict()
        
        assert data["type"] == "uses_channel"
        assert data["source_id"] == "campaign1"
        assert data["target_id"] == "linkedin"
        assert data["properties"]["priority"] == "high"


class TestDomainOntology:
    """Test DomainOntology"""
    
    def test_create_marketing_ontology(self):
        """Test creating marketing ontology"""
        ontology = DomainOntology("marketing")
        
        assert ontology.domain == "marketing"
        assert EntityType.CAMPAIGN in ontology.entity_types
        assert EntityType.CHANNEL in ontology.entity_types
        assert RelationshipType.TARGETS in ontology.relationship_types
        assert len(ontology.rules) > 0
    
    def test_create_education_ontology(self):
        """Test creating education ontology"""
        ontology = DomainOntology("education")
        
        assert EntityType.SUBJECT in ontology.entity_types
        assert EntityType.CONCEPT in ontology.entity_types
        assert RelationshipType.REQUIRES in ontology.relationship_types
    
    def test_create_sales_ontology(self):
        """Test creating sales ontology"""
        ontology = DomainOntology("sales")
        
        assert EntityType.LEAD in ontology.entity_types
        assert EntityType.OPPORTUNITY in ontology.entity_types
        assert RelationshipType.HAS_PAIN in ontology.relationship_types
    
    def test_validate_entity_type(self):
        """Test entity type validation"""
        ontology = DomainOntology("marketing")
        
        assert ontology.is_valid_entity_type(EntityType.CAMPAIGN) is True
        assert ontology.is_valid_entity_type(EntityType.CONCEPT) is False  # Education only
    
    def test_validate_relationship_type(self):
        """Test relationship type validation"""
        ontology = DomainOntology("education")
        
        assert ontology.is_valid_relationship_type(RelationshipType.REQUIRES) is True
        assert ontology.is_valid_relationship_type(RelationshipType.CLOSES) is False  # Sales only
    
    def test_get_reasoning_patterns(self):
        """Test getting reasoning patterns"""
        ontology = DomainOntology("marketing")
        patterns = ontology.get_reasoning_patterns()
        
        assert len(patterns) > 0
        assert any("B2B" in p for p in patterns)


class TestKnowledgeGraph:
    """Test KnowledgeGraph"""
    
    @pytest.fixture
    def graph(self):
        """Create knowledge graph for testing"""
        return KnowledgeGraph("marketing")
    
    def test_create_graph(self, graph):
        """Test creating knowledge graph"""
        assert graph.domain == "marketing"
        assert graph.ontology is not None
        assert len(graph.entities) == 0
        assert len(graph.relationships) == 0
    
    def test_add_entity(self, graph):
        """Test adding entity to graph"""
        entity = Entity(
            id="campaign1",
            type=EntityType.CAMPAIGN,
            name="Q4 Campaign"
        )
        
        success = graph.add_entity(entity)
        
        assert success is True
        assert "campaign1" in graph.entities
        assert graph.get_entity("campaign1") == entity
    
    def test_add_invalid_entity(self, graph):
        """Test adding invalid entity type"""
        # Try to add education entity to marketing graph
        entity = Entity(
            id="concept1",
            type=EntityType.CONCEPT,
            name="Algebra"
        )
        
        success = graph.add_entity(entity)
        
        assert success is False
        assert "concept1" not in graph.entities
    
    def test_add_relationship(self, graph):
        """Test adding relationship"""
        # Add entities first
        campaign = Entity(id="campaign1", type=EntityType.CAMPAIGN, name="Campaign")
        audience = Entity(id="audience1", type=EntityType.AUDIENCE, name="B2B")
        
        graph.add_entity(campaign)
        graph.add_entity(audience)
        
        # Add relationship
        rel = Relationship(
            id="rel1",
            type=RelationshipType.TARGETS,
            source_id="campaign1",
            target_id="audience1"
        )
        
        success = graph.add_relationship(rel)
        
        assert success is True
        assert "rel1" in graph.relationships
    
    def test_add_relationship_missing_entity(self, graph):
        """Test adding relationship with missing entities"""
        rel = Relationship(
            id="rel1",
            type=RelationshipType.TARGETS,
            source_id="nonexistent",
            target_id="also_nonexistent"
        )
        
        success = graph.add_relationship(rel)
        
        assert success is False
    
    def test_get_entities_by_type(self, graph):
        """Test getting entities by type"""
        # Add multiple campaigns
        for i in range(3):
            entity = Entity(
                id=f"campaign{i}",
                type=EntityType.CAMPAIGN,
                name=f"Campaign {i}"
            )
            graph.add_entity(entity)
        
        # Add one channel
        channel = Entity(id="linkedin", type=EntityType.CHANNEL, name="LinkedIn")
        graph.add_entity(channel)
        
        campaigns = graph.get_entities_by_type(EntityType.CAMPAIGN)
        channels = graph.get_entities_by_type(EntityType.CHANNEL)
        
        assert len(campaigns) == 3
        assert len(channels) == 1
    
    def test_get_outgoing_relationships(self, graph):
        """Test getting outgoing relationships"""
        # Setup: campaign -> audience, campaign -> channel
        campaign = Entity(id="c1", type=EntityType.CAMPAIGN, name="C1")
        audience = Entity(id="a1", type=EntityType.AUDIENCE, name="A1")
        channel = Entity(id="ch1", type=EntityType.CHANNEL, name="CH1")
        
        graph.add_entity(campaign)
        graph.add_entity(audience)
        graph.add_entity(channel)
        
        rel1 = Relationship(
            id="r1",
            type=RelationshipType.TARGETS,
            source_id="c1",
            target_id="a1"
        )
        rel2 = Relationship(
            id="r2",
            type=RelationshipType.USES_CHANNEL,
            source_id="c1",
            target_id="ch1"
        )
        
        graph.add_relationship(rel1)
        graph.add_relationship(rel2)
        
        # Get all outgoing
        outgoing = graph.get_outgoing_relationships("c1")
        assert len(outgoing) == 2
        
        # Get specific type
        targets = graph.get_outgoing_relationships("c1", RelationshipType.TARGETS)
        assert len(targets) == 1
        assert targets[0].target_id == "a1"
    
    def test_get_connected_entities(self, graph):
        """Test getting connected entities"""
        # Setup
        campaign = Entity(id="c1", type=EntityType.CAMPAIGN, name="C1")
        audience = Entity(id="a1", type=EntityType.AUDIENCE, name="A1")
        channel = Entity(id="ch1", type=EntityType.CHANNEL, name="CH1")
        
        graph.add_entity(campaign)
        graph.add_entity(audience)
        graph.add_entity(channel)
        
        rel1 = Relationship(
            id="r1",
            type=RelationshipType.TARGETS,
            source_id="c1",
            target_id="a1"
        )
        rel2 = Relationship(
            id="r2",
            type=RelationshipType.USES_CHANNEL,
            source_id="c1",
            target_id="ch1"
        )
        
        graph.add_relationship(rel1)
        graph.add_relationship(rel2)
        
        # Get connected entities
        connected = graph.get_connected_entities("c1", direction="outgoing")
        
        assert len(connected) == 2
        assert any(e.id == "a1" for e in connected)
        assert any(e.id == "ch1" for e in connected)
    
    def test_find_path(self, graph):
        """Test finding path between entities"""
        # Setup: c1 -> a1 (direct connection)
        campaign = Entity(id="c1", type=EntityType.CAMPAIGN, name="C1")
        audience = Entity(id="a1", type=EntityType.AUDIENCE, name="A1")
        
        graph.add_entity(campaign)
        graph.add_entity(audience)
        
        rel1 = Relationship(
            id="r1",
            type=RelationshipType.TARGETS,
            source_id="c1",
            target_id="a1"
        )
        
        graph.add_relationship(rel1)
        
        # Find path (simple 2-node path)
        path = graph.find_path("c1", "a1")
        
        assert path is not None
        assert len(path) == 2
        assert path[0] == "c1"
        assert path[1] == "a1"
    
    def test_find_path_no_connection(self, graph):
        """Test finding path when no connection exists"""
        # Add disconnected entities
        e1 = Entity(id="e1", type=EntityType.CAMPAIGN, name="E1")
        e2 = Entity(id="e2", type=EntityType.CHANNEL, name="E2")
        
        graph.add_entity(e1)
        graph.add_entity(e2)
        
        path = graph.find_path("e1", "e2")
        
        assert path is None
    
    def test_get_statistics(self, graph):
        """Test getting graph statistics"""
        # Add entities and relationships
        for i in range(3):
            campaign = Entity(id=f"c{i}", type=EntityType.CAMPAIGN, name=f"C{i}")
            graph.add_entity(campaign)
        
        for i in range(2):
            channel = Entity(id=f"ch{i}", type=EntityType.CHANNEL, name=f"CH{i}")
            graph.add_entity(channel)
        
        stats = graph.get_statistics()
        
        assert stats["domain"] == "marketing"
        assert stats["total_entities"] == 5
        assert stats["entity_types"]["campaign"] == 3
        assert stats["entity_types"]["channel"] == 2
    
    def test_to_dict(self, graph):
        """Test exporting graph to dict"""
        campaign = Entity(id="c1", type=EntityType.CAMPAIGN, name="C1")
        audience = Entity(id="a1", type=EntityType.AUDIENCE, name="A1")
        
        graph.add_entity(campaign)
        graph.add_entity(audience)
        
        rel = Relationship(
            id="r1",
            type=RelationshipType.TARGETS,
            source_id="c1",
            target_id="a1"
        )
        graph.add_relationship(rel)
        
        data = graph.to_dict()
        
        assert data["domain"] == "marketing"
        assert len(data["entities"]) == 2
        assert len(data["relationships"]) == 1


class TestGraphQueryEngine:
    """Test GraphQueryEngine"""
    
    @pytest.fixture
    def setup_graph(self):
        """Setup graph with data for testing"""
        graph = KnowledgeGraph("marketing")
        
        # Add entities
        campaign = Entity(id="c1", type=EntityType.CAMPAIGN, name="Campaign 1")
        audience = Entity(id="a1", type=EntityType.AUDIENCE, name="B2B", properties={"size": "enterprise"})
        channel = Entity(id="ch1", type=EntityType.CHANNEL, name="LinkedIn")
        
        graph.add_entity(campaign)
        graph.add_entity(audience)
        graph.add_entity(channel)
        
        # Add relationships
        rel1 = Relationship(id="r1", type=RelationshipType.TARGETS, source_id="c1", target_id="a1")
        rel2 = Relationship(id="r2", type=RelationshipType.USES_CHANNEL, source_id="c1", target_id="ch1")
        
        graph.add_relationship(rel1)
        graph.add_relationship(rel2)
        
        return graph, GraphQueryEngine(graph)
    
    def test_create_query_engine(self, setup_graph):
        """Test creating query engine"""
        graph, engine = setup_graph
        
        assert engine.graph == graph
    
    def test_query_by_properties(self, setup_graph):
        """Test querying entities by properties"""
        graph, engine = setup_graph
        
        results = engine.query_by_properties(
            EntityType.AUDIENCE,
            {"size": "enterprise"}
        )
        
        assert len(results) == 1
        assert results[0].id == "a1"
    
    def test_query_no_matches(self, setup_graph):
        """Test query with no matches"""
        graph, engine = setup_graph
        
        results = engine.query_by_properties(
            EntityType.AUDIENCE,
            {"size": "small_business"}
        )
        
        assert len(results) == 0
    
    def test_get_entity_context(self, setup_graph):
        """Test getting entity context"""
        graph, engine = setup_graph
        
        context = engine.get_entity_context("c1", depth=1)
        
        assert context["center_entity"]["id"] == "c1"
        assert len(context["related_entities"]) == 2  # audience + channel
        assert len(context["relationships"]) == 2
    
    def test_find_pattern(self, setup_graph):
        """Test finding pattern in graph"""
        graph, engine = setup_graph
        
        # Pattern: CAMPAIGN -> TARGETS -> AUDIENCE
        pattern = [(EntityType.CAMPAIGN, RelationshipType.TARGETS, EntityType.AUDIENCE)]
        
        matches = engine.find_pattern(pattern)
        
        assert len(matches) > 0
        assert matches[0][0].type == EntityType.CAMPAIGN
        assert matches[0][1].type == EntityType.AUDIENCE
