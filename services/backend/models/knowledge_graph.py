from beanie import Document, Link
from pydantic import Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from .video import Video


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph"""
    ENTITY = "entity"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    LOCATION = "location"
    OBJECT = "object"
    PERSON = "person"
    CONCEPT = "concept"


class RelationshipType(str, Enum):
    """Types of relationships between nodes"""
    APPEARS_WITH = "appears_with"
    INTERACTS_WITH = "interacts_with"
    LOCATED_AT = "located_at"
    OCCURS_BEFORE = "occurs_before"
    OCCURS_AFTER = "occurs_after"
    CAUSES = "causes"
    PART_OF = "part_of"
    MENTIONS = "mentions"
    TRANSFORMS_TO = "transforms_to"


class TemporalRange(dict):
    """Time range for node appearance"""
    start: float
    end: float
    
    def __init__(self, start: float, end: float):
        super().__init__(start=start, end=end)
        self.start = start
        self.end = end


class Connection(dict):
    """Connection to another node"""
    target_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    confidence: float = 1.0
    
    def __init__(self, **data):
        super().__init__(**data)
        self.__dict__.update(data)


class KnowledgeGraphNode(Document):
    """Knowledge graph node as defined in PRD"""
    
    # Video reference
    video_id: str
    video: Optional[Link[Video]] = None
    
    # Node properties
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    # Embeddings for semantic search
    embeddings: List[float] = Field(default_factory=list)
    embedding_model: Optional[str] = None
    
    # Graph-RAG integration
    vector_db_id: Optional[str] = None  # Qdrant point ID
    neo4j_node_id: Optional[str] = None  # Neo4j node ID for Graph-RAG
    
    # Temporal information
    temporal_range: Optional[Dict[str, float]] = None
    scene_numbers: List[int] = Field(default_factory=list)
    
    # Graph connections
    connections: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    confidence_score: float = Field(ge=0, le=1, default=1.0)
    source_provider: Optional[str] = None
    extraction_method: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "knowledge_graph"
        indexes = [
            [("video_id", 1), ("node_type", 1)],
            [("video_id", 1), ("label", 1)],
            [("node_type", 1), ("label", 1)],
            [("temporal_range.start", 1)],
        ]
    
    @field_validator('temporal_range')
    @classmethod
    def validate_temporal_range(cls, v):
        if v and v.get('end', 0) <= v.get('start', 0):
            raise ValueError("Temporal range end must be greater than start")
        return v
    
    def add_connection(self, target_node_id: str, relationship_type: RelationshipType, 
                      properties: Optional[Dict[str, Any]] = None, confidence: float = 1.0):
        """Add a connection to another node"""
        connection = {
            "target_node_id": target_node_id,
            "relationship_type": relationship_type.value,
            "properties": properties or {},
            "confidence": confidence
        }
        self.connections.append(connection)
        self.updated_at = datetime.utcnow()
    
    def get_connections_by_type(self, relationship_type: RelationshipType) -> List[Dict[str, Any]]:
        """Get all connections of a specific type"""
        return [c for c in self.connections if c["relationship_type"] == relationship_type.value]
    
    def appears_in_time_range(self, start: float, end: float) -> bool:
        """Check if node appears within a time range"""
        if not self.temporal_range:
            return False
        node_start = self.temporal_range.get("start", float('inf'))
        node_end = self.temporal_range.get("end", float('-inf'))
        return not (node_end < start or node_start > end)