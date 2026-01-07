"""
Knowledge Graph - Story 4.4

Graph-based knowledge representation linking entities, concepts, and relationships.
Part of Epic 4: Learning & Memory.
"""
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in knowledge graph."""
    ENTITY = "entity"  # Concrete entities (users, agents, etc.)
    CONCEPT = "concept"  # Abstract concepts
    EVENT = "event"  # Events/actions
    SKILL = "skill"  # Skills/capabilities
    GOAL = "goal"  # Goals/objectives


class RelationType(Enum):
    """Types of relationships."""
    IS_A = "is_a"  # Inheritance
    HAS_A = "has_a"  # Composition
    RELATED_TO = "related_to"  # Generic relation
    CAUSED_BY = "caused_by"  # Causation
    REQUIRES = "requires"  # Dependency
    PRODUCES = "produces"  # Output
    SIMILAR_TO = "similar_to"  # Similarity


@dataclass
class KnowledgeNode:
    """Node in knowledge graph."""
    node_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeRelation:
    """Relationship between nodes."""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0  # Strength of relation
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class KnowledgeGraph:
    """
    Graph-based knowledge representation.
    
    Features:
    - Add/remove nodes and relationships
    - Query by node/relationship type
    - Find paths between nodes
    - Discover patterns
    - Semantic similarity
    - Knowledge consolidation
    """
    
    def __init__(self):
        """Initialize knowledge graph."""
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relations: Dict[str, KnowledgeRelation] = {}
        
        # Indexes for efficient lookup
        self._nodes_by_type: Dict[NodeType, Set[str]] = {
            node_type: set() for node_type in NodeType
        }
        self._relations_by_type: Dict[RelationType, Set[str]] = {
            rel_type: set() for rel_type in RelationType
        }
        self._outgoing_relations: Dict[str, Set[str]] = {}  # node_id -> relation_ids
        self._incoming_relations: Dict[str, Set[str]] = {}  # node_id -> relation_ids
        
        self.node_counter = 0
        self.relation_counter = 0
        
        logger.info("KnowledgeGraph initialized")
    
    def add_node(
        self,
        node_type: NodeType,
        label: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add node to graph.
        
        Args:
            node_type: Type of node
            label: Human-readable label
            properties: Additional properties
            
        Returns:
            Node ID
        """
        node_id = f"{node_type.value}_{self.node_counter}"
        self.node_counter += 1
        
        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            properties=properties or {}
        )
        
        self.nodes[node_id] = node
        self._nodes_by_type[node_type].add(node_id)
        
        logger.debug(f"Added node: {node_id} ({label})")
        
        return node_id
    
    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add relationship between nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation_type: Type of relationship
            weight: Relationship strength (0-1)
            properties: Additional properties
            
        Returns:
            Relation ID
        """
        if source_id not in self.nodes:
            raise ValueError(f"Source node not found: {source_id}")
        if target_id not in self.nodes:
            raise ValueError(f"Target node not found: {target_id}")
        
        relation_id = f"rel_{self.relation_counter}"
        self.relation_counter += 1
        
        relation = KnowledgeRelation(
            relation_id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            properties=properties or {}
        )
        
        self.relations[relation_id] = relation
        self._relations_by_type[relation_type].add(relation_id)
        
        # Update indexes
        if source_id not in self._outgoing_relations:
            self._outgoing_relations[source_id] = set()
        self._outgoing_relations[source_id].add(relation_id)
        
        if target_id not in self._incoming_relations:
            self._incoming_relations[target_id] = set()
        self._incoming_relations[target_id].add(relation_id)
        
        logger.debug(
            f"Added relation: {source_id} --[{relation_type.value}]--> {target_id}"
        )
        
        return relation_id
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[KnowledgeNode]:
        """Get all nodes of a specific type."""
        node_ids = self._nodes_by_type[node_type]
        return [self.nodes[nid] for nid in node_ids]
    
    def get_relations_for_node(
        self,
        node_id: str,
        direction: str = "both"
    ) -> List[KnowledgeRelation]:
        """
        Get relations connected to a node.
        
        Args:
            node_id: Node ID
            direction: 'outgoing', 'incoming', or 'both'
            
        Returns:
            List of relations
        """
        relation_ids = set()
        
        if direction in ["outgoing", "both"]:
            relation_ids.update(self._outgoing_relations.get(node_id, set()))
        
        if direction in ["incoming", "both"]:
            relation_ids.update(self._incoming_relations.get(node_id, set()))
        
        return [self.relations[rid] for rid in relation_ids]
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """
        Find shortest path between two nodes (BFS).
        
        Args:
            start_id: Starting node ID
            end_id: Target node ID
            max_depth: Maximum path length
            
        Returns:
            List of node IDs forming path, or None
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None
        
        if start_id == end_id:
            return [start_id]
        
        # BFS
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Get neighbors
            relations = self.get_relations_for_node(current_id, "outgoing")
            
            for relation in relations:
                neighbor_id = relation.target_id
                
                if neighbor_id == end_id:
                    return path + [neighbor_id]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None
    
    def find_similar_nodes(
        self,
        node_id: str,
        min_similarity: float = 0.5,
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find similar nodes based on shared relations.
        
        Args:
            node_id: Reference node ID
            min_similarity: Minimum similarity score
            max_results: Maximum results to return
            
        Returns:
            List of (node_id, similarity_score) tuples
        """
        if node_id not in self.nodes:
            return []
        
        # Get relations of reference node
        ref_relations = self.get_relations_for_node(node_id)
        ref_neighbors = {
            r.target_id for r in ref_relations if r.source_id == node_id
        }
        ref_neighbors.update({
            r.source_id for r in ref_relations if r.target_id == node_id
        })
        
        if not ref_neighbors:
            return []
        
        # Calculate similarity with other nodes
        similarities = []
        
        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue
            
            # Get neighbors of other node
            other_relations = self.get_relations_for_node(other_id)
            other_neighbors = {
                r.target_id for r in other_relations if r.source_id == other_id
            }
            other_neighbors.update({
                r.source_id for r in other_relations if r.target_id == other_id
            })
            
            if not other_neighbors:
                continue
            
            # Jaccard similarity
            intersection = len(ref_neighbors & other_neighbors)
            union = len(ref_neighbors | other_neighbors)
            
            if union > 0:
                similarity = intersection / union
                
                if similarity >= min_similarity:
                    similarities.append((other_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:max_results]
    
    def get_subgraph(
        self,
        node_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Extract subgraph around a node.
        
        Args:
            node_id: Center node ID
            max_depth: Maximum distance from center
            
        Returns:
            Subgraph as dict with nodes and relations
        """
        if node_id not in self.nodes:
            return {"nodes": [], "relations": []}
        
        # BFS to collect nodes
        visited_nodes = {node_id}
        queue = [(node_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # Get connected nodes
            relations = self.get_relations_for_node(current_id)
            
            for relation in relations:
                neighbor_id = (
                    relation.target_id
                    if relation.source_id == current_id
                    else relation.source_id
                )
                
                if neighbor_id not in visited_nodes:
                    visited_nodes.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))
        
        # Collect relations within subgraph
        subgraph_relations = []
        for relation in self.relations.values():
            if (relation.source_id in visited_nodes and
                relation.target_id in visited_nodes):
                subgraph_relations.append(relation)
        
        return {
            "nodes": [self.nodes[nid] for nid in visited_nodes],
            "relations": subgraph_relations
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": len(self.nodes),
            "total_relations": len(self.relations),
            "nodes_by_type": {
                node_type.value: len(node_ids)
                for node_type, node_ids in self._nodes_by_type.items()
            },
            "relations_by_type": {
                rel_type.value: len(rel_ids)
                for rel_type, rel_ids in self._relations_by_type.items()
            }
        }
