"""MongoDB models for dev-cli - extracted to avoid import issues"""
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class SourceType(str, Enum):
    """Types of knowledge sources"""
    PDF = "pdf"
    GITHUB = "github"
    INTERNAL = "internal"
    DOCUMENTATION = "documentation"
    CURATED = "curated"


# MongoDB Models
class ProjectKnowledge(Document):
    """Stores extracted project knowledge with Graph-RAG support"""
    
    source_file: str
    source_repo: str
    source_type: SourceType = SourceType.INTERNAL
    category: str
    title: str
    content: str
    importance: int = Field(ge=1, le=5)
    tags: list[str] = []
    
    # Graph-RAG fields
    vector_db_id: Optional[str] = None  # Qdrant point ID
    graph_node_id: Optional[str] = None  # Neo4j node ID
    entities: List[str] = []  # Extracted entities for graph
    relationships: List[Dict[str, str]] = []  # Related entities
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    processing_metadata: Dict[str, Any] = {}
    
    class Settings:
        name = "project_knowledge"
        indexes = [
            "category",
            "importance",
            "tags",
            [("category", 1), ("importance", -1)]
        ]


class ExtractionReport(Document):
    """Tracks knowledge extraction runs"""
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"
    statistics: Dict[str, Any] = {}
    errors: list[str] = []
    
    class Settings:
        name = "extraction_reports"