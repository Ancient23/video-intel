# MongoDB models using Beanie ODM

from .project_status import ProjectStatus, ProjectPhase, ComponentStatus
from .video import Video, VideoStatus
from .scene import Scene, Shot
from .knowledge_graph import KnowledgeGraphNode, NodeType, RelationshipType
from .processing_job import ProcessingJob, JobStatus, JobType

# List of all document models for Beanie initialization
document_models = [
    ProjectStatus,
    Video,
    Scene,
    KnowledgeGraphNode,
    ProcessingJob,
]

__all__ = [
    # Project Status
    "ProjectStatus",
    "ProjectPhase", 
    "ComponentStatus",
    
    # Video
    "Video",
    "VideoStatus",
    
    # Scene
    "Scene",
    "Shot",
    
    # Knowledge Graph
    "KnowledgeGraphNode",
    "NodeType",
    "RelationshipType",
    
    # Processing Job
    "ProcessingJob",
    "JobStatus",
    "JobType",
    
    # Initialization
    "document_models",
]