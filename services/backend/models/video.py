from beanie import Document, Indexed
from pydantic import Field, HttpUrl, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class VideoStatus(str, Enum):
    """Video processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(Document):
    """Main video document"""
    
    # Basic metadata
    title: str
    description: Optional[str] = None
    s3_url: str
    thumbnail_url: Optional[str] = None
    
    # Video properties
    duration: float = Field(gt=0, description="Duration in seconds")
    fps: float = Field(gt=0, default=30.0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    
    # Processing status
    status: VideoStatus = Field(default=VideoStatus.UPLOADED)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Relationships
    scene_ids: List[str] = Field(default_factory=list)
    total_scenes: int = Field(default=0)
    total_shots: int = Field(default=0)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    project_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "videos"
        indexes = [
            [("status", 1), ("created_at", -1)],
            [("project_id", 1)],
            [("created_at", -1)],
        ]
    
    @field_validator('s3_url')
    @classmethod
    def validate_s3_url(cls, v):
        if not v.startswith(('s3://', 'https://')):
            raise ValueError("URL must be an S3 URL or HTTPS URL")
        return v
    
    def mark_processing(self):
        """Mark video as processing"""
        self.status = VideoStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark video as completed"""
        self.status = VideoStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error: str):
        """Mark video as failed"""
        self.status = VideoStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.utcnow()