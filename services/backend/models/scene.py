from beanie import Document, Link
from pydantic import Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from .video import Video


class Shot(dict):
    """Shot within a scene"""
    shot_id: str
    start_time: float
    end_time: float
    keyframe_url: str
    dense_caption: str
    visual_embeddings: List[float]
    detected_objects: List[Dict[str, Any]]
    provider_metadata: Dict[str, Any]
    
    def __init__(self, **data):
        super().__init__(**data)
        self.__dict__.update(data)


class Scene(Document):
    """Scene document as defined in PRD"""
    
    # Video reference
    video_id: str
    video: Optional[Link[Video]] = None
    
    # Scene metadata
    scene_number: int
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    
    # Shots within the scene
    shots: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Scene-level analysis
    summary: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    mood: Optional[str] = None
    
    # Graph connections
    graph_node_ids: List[str] = Field(default_factory=list)
    
    # Processing metadata
    processed_providers: List[str] = Field(default_factory=list)
    processing_time: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "scenes"
        indexes = [
            [("video_id", 1), ("scene_number", 1)],
            [("video_id", 1), ("start_time", 1)],
            [("themes", 1)],
        ]
    
    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("End time must be greater than start time")
        return v
    
    def add_shot(self, shot: Dict[str, Any]):
        """Add a shot to the scene"""
        required_fields = ['shot_id', 'start_time', 'end_time', 'keyframe_url', 'dense_caption']
        for field in required_fields:
            if field not in shot:
                raise ValueError(f"Shot missing required field: {field}")
        
        self.shots.append(shot)
        self.updated_at = datetime.utcnow()
    
    def get_duration(self) -> float:
        """Get scene duration in seconds"""
        return self.end_time - self.start_time
    
    def get_shot_count(self) -> int:
        """Get number of shots in scene"""
        return len(self.shots)