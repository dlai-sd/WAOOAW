"""
Domain-Specific Knowledge Graphs

Specialized knowledge graphs for Marketing, Education, and Sales domains.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class EntityType(str, Enum):
    """Types of entities in knowledge graphs"""
    # Marketing entities
    CAMPAIGN = "campaign"
    CHANNEL = "channel"
    CONTENT_TYPE = "content_type"
    AUDIENCE = "audience"
    METRIC = "metric"
    BRAND = "brand"
    
    # Education entities
    SUBJECT = "subject"
    CONCEPT = "concept"
    SKILL = "skill"
    LEARNING_OBJECTIVE = "learning_objective"
    PREREQUISITE = "prerequisite"
    DIFFICULTY_LEVEL = "difficulty_level"
    
    # Sales entities
    LEAD = "lead"
    ACCOUNT = "account"
    OPPORTUNITY = "opportunity"
    PRODUCT = "product"
    PAIN_POINT = "pain_point"
    DECISION_MAKER = "decision_maker"
    
    # Common entities
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"


class RelationshipType(str, Enum):
    """Types of relationships between entities"""
    # Marketing relationships
    TARGETS = "targets"
    USES_CHANNEL = "uses_channel"
    CREATES_CONTENT = "creates_content"
    MEASURES = "measures"
    COMPETES_WITH = "competes_with"
    
    # Education relationships
    REQUIRES = "requires"
    TEACHES = "teaches"
    BUILDS_ON = "builds_on"
    ASSESSES = "assesses"
    RELATES_TO = "relates_to"
    
    # Sales relationships
    WORKS_FOR = "works_for"
    INTERESTED_IN = "interested_in"
    HAS_PAIN = "has_pain"
    DECIDES_ON = "decides_on"
    CLOSES = "closes"
    
    # Common relationships
    PART_OF = "part_of"
    INFLUENCES = "influences"
    DEPENDS_ON = "depends_on"


@dataclass
class Entity:
    """Entity in knowledge graph"""
    id: str
    type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Relationship:
    """Relationship between entities"""
    id: str
    type: RelationshipType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0  # Relationship strength (0-1)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "strength": self.strength,
            "created_at": self.created_at.isoformat()
        }


class DomainOntology:
    """
    Domain-specific ontology defining valid entity and relationship types.
    
    Provides rules and constraints for knowledge graph construction.
    """
    
    def __init__(self, domain: str):
        """
        Initialize domain ontology.
        
        Args:
            domain: Domain name (marketing, education, sales)
        """
        self.domain = domain
        self.entity_types: Set[EntityType] = set()
        self.relationship_types: Set[RelationshipType] = set()
        self.rules: List[Dict[str, Any]] = []
        
        self._initialize_domain()
    
    def _initialize_domain(self):
        """Initialize domain-specific entity and relationship types"""
        if self.domain == "marketing":
            self.entity_types = {
                EntityType.CAMPAIGN,
                EntityType.CHANNEL,
                EntityType.CONTENT_TYPE,
                EntityType.AUDIENCE,
                EntityType.METRIC,
                EntityType.BRAND,
                EntityType.PERSON,
                EntityType.ORGANIZATION
            }
            self.relationship_types = {
                RelationshipType.TARGETS,
                RelationshipType.USES_CHANNEL,
                RelationshipType.CREATES_CONTENT,
                RelationshipType.MEASURES,
                RelationshipType.COMPETES_WITH,
                RelationshipType.INFLUENCES
            }
            self.rules = [
                {
                    "name": "campaign_requires_channel",
                    "description": "Every campaign must use at least one channel",
                    "constraint": "CAMPAIGN -> USES_CHANNEL -> CHANNEL"
                },
                {
                    "name": "campaign_targets_audience",
                    "description": "Every campaign must target an audience",
                    "constraint": "CAMPAIGN -> TARGETS -> AUDIENCE"
                }
            ]
        
        elif self.domain == "education":
            self.entity_types = {
                EntityType.SUBJECT,
                EntityType.CONCEPT,
                EntityType.SKILL,
                EntityType.LEARNING_OBJECTIVE,
                EntityType.PREREQUISITE,
                EntityType.DIFFICULTY_LEVEL,
                EntityType.PERSON
            }
            self.relationship_types = {
                RelationshipType.REQUIRES,
                RelationshipType.TEACHES,
                RelationshipType.BUILDS_ON,
                RelationshipType.ASSESSES,
                RelationshipType.RELATES_TO,
                RelationshipType.PART_OF
            }
            self.rules = [
                {
                    "name": "concept_has_prerequisites",
                    "description": "Advanced concepts require prerequisite knowledge",
                    "constraint": "CONCEPT -> REQUIRES -> PREREQUISITE"
                },
                {
                    "name": "skill_builds_on_concept",
                    "description": "Skills are built on fundamental concepts",
                    "constraint": "SKILL -> BUILDS_ON -> CONCEPT"
                }
            ]
        
        elif self.domain == "sales":
            self.entity_types = {
                EntityType.LEAD,
                EntityType.ACCOUNT,
                EntityType.OPPORTUNITY,
                EntityType.PRODUCT,
                EntityType.PAIN_POINT,
                EntityType.DECISION_MAKER,
                EntityType.PERSON,
                EntityType.ORGANIZATION
            }
            self.relationship_types = {
                RelationshipType.WORKS_FOR,
                RelationshipType.INTERESTED_IN,
                RelationshipType.HAS_PAIN,
                RelationshipType.DECIDES_ON,
                RelationshipType.CLOSES,
                RelationshipType.INFLUENCES
            }
            self.rules = [
                {
                    "name": "lead_has_pain_point",
                    "description": "Qualified leads have identifiable pain points",
                    "constraint": "LEAD -> HAS_PAIN -> PAIN_POINT"
                },
                {
                    "name": "decision_maker_works_for_account",
                    "description": "Decision makers belong to accounts",
                    "constraint": "DECISION_MAKER -> WORKS_FOR -> ACCOUNT"
                }
            ]
    
    def is_valid_entity_type(self, entity_type: EntityType) -> bool:
        """Check if entity type is valid for domain"""
        return entity_type in self.entity_types
    
    def is_valid_relationship_type(self, rel_type: RelationshipType) -> bool:
        """Check if relationship type is valid for domain"""
        return rel_type in self.relationship_types
    
    def get_reasoning_patterns(self) -> List[str]:
        """Get domain-specific reasoning patterns"""
        patterns = []
        
        if self.domain == "marketing":
            patterns = [
                "If targeting B2B audience, prioritize LinkedIn and email channels",
                "If brand awareness goal, focus on reach metrics (impressions, views)",
                "If conversion goal, optimize for engagement and CTR",
                "If competing with established brand, differentiate through unique value prop",
                "If launching new product, build awareness campaign before conversion campaign"
            ]
        
        elif self.domain == "education":
            patterns = [
                "If student struggles with concept, review prerequisites first",
                "If concept is abstract, use concrete examples and analogies",
                "If skill requires practice, provide step-by-step exercises",
                "If assessment score is low, identify knowledge gaps systematically",
                "If learning objective is complex, break down into sub-objectives"
            ]
        
        elif self.domain == "sales":
            patterns = [
                "If lead has budget and authority, prioritize as high-value opportunity",
                "If pain point is urgent, emphasize quick time-to-value",
                "If multiple decision makers, identify champion and build consensus",
                "If objection is price, demonstrate ROI with case studies",
                "If competitor is entrenched, focus on differentiation and switching benefits"
            ]
        
        return patterns


class KnowledgeGraph:
    """
    Domain-specific knowledge graph with entities and relationships.
    
    Supports querying, reasoning, and knowledge fusion.
    """
    
    def __init__(self, domain: str, ontology: Optional[DomainOntology] = None):
        """
        Initialize knowledge graph.
        
        Args:
            domain: Domain name (marketing, education, sales)
            ontology: Domain ontology (created if not provided)
        """
        self.domain = domain
        self.ontology = ontology or DomainOntology(domain)
        
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # Indexes for fast lookup
        self._entity_type_index: Dict[EntityType, Set[str]] = {}
        self._outgoing_rels: Dict[str, List[str]] = {}  # entity_id -> [rel_ids]
        self._incoming_rels: Dict[str, List[str]] = {}  # entity_id -> [rel_ids]
    
    def add_entity(self, entity: Entity) -> bool:
        """
        Add entity to graph.
        
        Args:
            entity: Entity to add
            
        Returns:
            True if added successfully
        """
        if not self.ontology.is_valid_entity_type(entity.type):
            return False
        
        self.entities[entity.id] = entity
        
        # Update index
        if entity.type not in self._entity_type_index:
            self._entity_type_index[entity.type] = set()
        self._entity_type_index[entity.type].add(entity.id)
        
        return True
    
    def add_relationship(self, relationship: Relationship) -> bool:
        """
        Add relationship to graph.
        
        Args:
            relationship: Relationship to add
            
        Returns:
            True if added successfully
        """
        if not self.ontology.is_valid_relationship_type(relationship.type):
            return False
        
        # Check that source and target entities exist
        if relationship.source_id not in self.entities:
            return False
        if relationship.target_id not in self.entities:
            return False
        
        self.relationships[relationship.id] = relationship
        
        # Update indexes
        if relationship.source_id not in self._outgoing_rels:
            self._outgoing_rels[relationship.source_id] = []
        self._outgoing_rels[relationship.source_id].append(relationship.id)
        
        if relationship.target_id not in self._incoming_rels:
            self._incoming_rels[relationship.target_id] = []
        self._incoming_rels[relationship.target_id].append(relationship.id)
        
        return True
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of specific type"""
        entity_ids = self._entity_type_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids]
    
    def get_outgoing_relationships(
        self,
        entity_id: str,
        rel_type: Optional[RelationshipType] = None
    ) -> List[Relationship]:
        """Get outgoing relationships from entity"""
        rel_ids = self._outgoing_rels.get(entity_id, [])
        relationships = [self.relationships[rid] for rid in rel_ids]
        
        if rel_type:
            relationships = [r for r in relationships if r.type == rel_type]
        
        return relationships
    
    def get_incoming_relationships(
        self,
        entity_id: str,
        rel_type: Optional[RelationshipType] = None
    ) -> List[Relationship]:
        """Get incoming relationships to entity"""
        rel_ids = self._incoming_rels.get(entity_id, [])
        relationships = [self.relationships[rid] for rid in rel_ids]
        
        if rel_type:
            relationships = [r for r in relationships if r.type == rel_type]
        
        return relationships
    
    def get_connected_entities(
        self,
        entity_id: str,
        rel_type: Optional[RelationshipType] = None,
        direction: str = "outgoing"
    ) -> List[Entity]:
        """
        Get entities connected to given entity.
        
        Args:
            entity_id: Source entity ID
            rel_type: Relationship type filter
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            List of connected entities
        """
        connected = []
        
        if direction in ["outgoing", "both"]:
            rels = self.get_outgoing_relationships(entity_id, rel_type)
            connected.extend([
                self.entities[r.target_id] for r in rels
                if r.target_id in self.entities
            ])
        
        if direction in ["incoming", "both"]:
            rels = self.get_incoming_relationships(entity_id, rel_type)
            connected.extend([
                self.entities[r.source_id] for r in rels
                if r.source_id in self.entities
            ])
        
        return connected
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3
    ) -> Optional[List[str]]:
        """
        Find shortest path between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_depth: Maximum path depth
            
        Returns:
            List of entity IDs forming path, or None if no path found
        """
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        # BFS
        queue = [(source_id, [source_id])]
        visited = {source_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Get connected entities
            connected = self.get_connected_entities(current_id, direction="outgoing")
            
            for entity in connected:
                if entity.id in visited:
                    continue
                
                new_path = path + [entity.id]
                
                if entity.id == target_id:
                    return new_path
                
                queue.append((entity.id, new_path))
                visited.add(entity.id)
        
        return None
    
    def to_dict(self) -> dict:
        """Export graph to dictionary"""
        return {
            "domain": self.domain,
            "entities": [e.to_dict() for e in self.entities.values()],
            "relationships": [r.to_dict() for r in self.relationships.values()]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        entity_counts = {}
        for entity_type in self._entity_type_index:
            entity_counts[entity_type.value] = len(self._entity_type_index[entity_type])
        
        rel_counts = {}
        for rel in self.relationships.values():
            rel_type = rel.type.value
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1
        
        return {
            "domain": self.domain,
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": entity_counts,
            "relationship_types": rel_counts
        }


class GraphQueryEngine:
    """
    Query engine for knowledge graphs.
    
    Supports pattern matching, reasoning, and knowledge fusion.
    """
    
    def __init__(self, graph: KnowledgeGraph):
        """
        Initialize query engine.
        
        Args:
            graph: Knowledge graph to query
        """
        self.graph = graph
    
    def find_pattern(
        self,
        pattern: List[Tuple[EntityType, RelationshipType, EntityType]]
    ) -> List[List[Entity]]:
        """
        Find entities matching pattern.
        
        Pattern format: [(source_type, rel_type, target_type), ...]
        
        Args:
            pattern: Pattern to match
            
        Returns:
            List of entity sequences matching pattern
        """
        if not pattern:
            return []
        
        matches = []
        
        # Start with all entities of first type
        source_type, rel_type, target_type = pattern[0]
        source_entities = self.graph.get_entities_by_type(source_type)
        
        for source in source_entities:
            # Find targets connected by relationship
            rels = self.graph.get_outgoing_relationships(source.id, rel_type)
            
            for rel in rels:
                target = self.graph.get_entity(rel.target_id)
                if target and target.type == target_type:
                    # Match found for first pattern element
                    if len(pattern) == 1:
                        matches.append([source, target])
                    else:
                        # Recursively match rest of pattern
                        # (Simplified - full implementation would continue matching)
                        matches.append([source, target])
        
        return matches
    
    def query_by_properties(
        self,
        entity_type: EntityType,
        properties: Dict[str, Any]
    ) -> List[Entity]:
        """
        Query entities by type and properties.
        
        Args:
            entity_type: Entity type to search
            properties: Property filters (key-value pairs)
            
        Returns:
            List of matching entities
        """
        entities = self.graph.get_entities_by_type(entity_type)
        
        matches = []
        for entity in entities:
            # Check if all properties match
            match = True
            for key, value in properties.items():
                if entity.properties.get(key) != value:
                    match = False
                    break
            
            if match:
                matches.append(entity)
        
        return matches
    
    def apply_reasoning_rules(self, entity_id: str) -> List[str]:
        """
        Apply domain-specific reasoning rules to entity.
        
        Args:
            entity_id: Entity to apply reasoning to
            
        Returns:
            List of inferred insights
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return []
        
        insights = []
        
        # Get reasoning patterns from ontology
        patterns = self.graph.ontology.get_reasoning_patterns()
        
        # Apply patterns based on entity connections
        # (Simplified - full implementation would match patterns to graph structure)
        
        # Example: If entity has specific relationships, apply relevant patterns
        outgoing = self.graph.get_outgoing_relationships(entity_id)
        incoming = self.graph.get_incoming_relationships(entity_id)
        
        if outgoing or incoming:
            # Sample insight based on connectivity
            insights.append(
                f"Entity {entity.name} has {len(outgoing)} outgoing and {len(incoming)} incoming relationships"
            )
        
        return insights
    
    def get_entity_context(
        self,
        entity_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Get full context around entity (neighbors up to depth).
        
        Args:
            entity_id: Entity to get context for
            depth: Maximum depth to traverse
            
        Returns:
            Context dictionary with entities and relationships
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return {}
        
        context_entities = {entity_id: entity}
        context_relationships = []
        
        # BFS to depth
        queue = [(entity_id, 0)]
        visited = {entity_id}
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            # Get connected entities
            outgoing = self.graph.get_outgoing_relationships(current_id)
            incoming = self.graph.get_incoming_relationships(current_id)
            
            for rel in outgoing + incoming:
                context_relationships.append(rel)
                
                # Add connected entity
                other_id = (
                    rel.target_id if rel.source_id == current_id
                    else rel.source_id
                )
                
                if other_id not in visited:
                    other_entity = self.graph.get_entity(other_id)
                    if other_entity:
                        context_entities[other_id] = other_entity
                        queue.append((other_id, current_depth + 1))
                        visited.add(other_id)
        
        return {
            "center_entity": entity.to_dict(),
            "related_entities": [
                e.to_dict() for e in context_entities.values()
                if e.id != entity_id
            ],
            "relationships": [r.to_dict() for r in context_relationships]
        }
