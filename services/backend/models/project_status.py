from beanie import Document, Indexed
from pydantic import Field, field_validator
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class ProjectPhase(str, Enum):
    """Project implementation phases"""
    SETUP = "setup"
    FOUNDATION = "foundation"
    KNOWLEDGE_BUILDING = "knowledge_building"
    RAG_IMPLEMENTATION = "rag_implementation"
    RUNTIME_FEATURES = "runtime_features"
    PRODUCTION = "production"


class ComponentStatus(str, Enum):
    """Component implementation status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ProjectStatus(Document):
    """Track overall project implementation status"""
    
    # Project identification
    project_name: str = Field(default="video-intelligence-platform")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Current phase
    current_phase: ProjectPhase = Field(default=ProjectPhase.SETUP)
    phase_started_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Component statuses
    components: Dict[str, ComponentStatus] = Field(default_factory=lambda: {
        "mongodb_setup": ComponentStatus.NOT_STARTED,
        "video_chunking": ComponentStatus.NOT_STARTED,
        "provider_architecture": ComponentStatus.NOT_STARTED,
        "knowledge_graph": ComponentStatus.NOT_STARTED,
        "embeddings": ComponentStatus.NOT_STARTED,
        "rag_system": ComponentStatus.NOT_STARTED,
        "api_endpoints": ComponentStatus.NOT_STARTED,
        "websocket_support": ComponentStatus.NOT_STARTED,
        "conversation_engine": ComponentStatus.NOT_STARTED,
        "testing_suite": ComponentStatus.NOT_STARTED,
    })
    
    # Progress tracking
    completed_tasks: List[str] = Field(default_factory=list)
    current_tasks: List[str] = Field(default_factory=list)
    blocked_tasks: List[Dict[str, str]] = Field(default_factory=list)  # task and reason
    
    # Metrics
    lines_of_code: int = Field(default=0)
    test_coverage: float = Field(default=0.0)
    api_endpoints_completed: int = Field(default=0)
    providers_integrated: List[str] = Field(default_factory=list)
    
    # Notes and issues
    notes: List[Dict[str, Any]] = Field(default_factory=list)
    known_issues: List[Dict[str, str]] = Field(default_factory=list)
    
    class Settings:
        name = "project_status"
        indexes = [
            [("project_name", 1)],
            [("updated_at", -1)],
        ]
    
    @field_validator('test_coverage')
    @classmethod
    def validate_coverage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Test coverage must be between 0 and 100")
        return v
    
    def update_component(self, component: str, status: ComponentStatus):
        """Update a component's status"""
        if component not in self.components:
            raise ValueError(f"Unknown component: {component}")
        self.components[component] = status
        self.updated_at = datetime.utcnow()
    
    def add_completed_task(self, task: str):
        """Mark a task as completed"""
        if task in self.current_tasks:
            self.current_tasks.remove(task)
        if task not in self.completed_tasks:
            self.completed_tasks.append(task)
        self.updated_at = datetime.utcnow()
    
    def add_note(self, note: str, category: str = "general"):
        """Add a development note"""
        self.notes.append({
            "timestamp": datetime.utcnow(),
            "category": category,
            "note": note
        })
        self.updated_at = datetime.utcnow()