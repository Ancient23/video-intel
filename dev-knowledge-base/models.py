"""MongoDB models for dev-cli - extracted to avoid import issues"""
from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional


# MongoDB Models
class ProjectKnowledge(Document):
    """Stores extracted project knowledge"""
    
    source_file: str
    source_repo: str
    category: str
    title: str
    content: str
    importance: int = Field(ge=1, le=5)
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
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