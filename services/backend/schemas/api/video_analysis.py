"""
Request and response schemas for video analysis API endpoints
"""
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from ..analysis import (
    VideoType, AnalysisGoal, ProviderType, ProviderCapability,
    SceneDetection, ObjectDetection, AnalysisResult
)
from ...models.processing_job import JobStatus, JobType
from ...models.video import VideoStatus


# Request Schemas
class VideoAnalysisRequest(BaseModel):
    """Request to start video analysis"""
    video_url: str = Field(description="S3 URL of the video to analyze")
    user_prompt: str = Field(description="Natural language prompt describing what to analyze")
    video_type: Optional[VideoType] = Field(default=VideoType.GENERAL, description="Type of video content")
    chunk_duration: Optional[int] = Field(default=10, ge=5, le=60, description="Duration of each chunk in seconds")
    chunk_overlap: Optional[int] = Field(default=2, ge=0, le=10, description="Overlap between chunks in seconds")
    max_frames_per_chunk: Optional[int] = Field(default=30, ge=10, le=100, description="Maximum frames to process per chunk")
    selected_providers: Optional[List[ProviderType]] = Field(default=None, description="Specific providers to use")
    cost_limit: Optional[float] = Field(default=None, ge=0, description="Maximum cost limit for analysis")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @field_validator('video_url')
    @classmethod
    def validate_video_url(cls, v):
        if not v.startswith(('s3://', 'https://')):
            raise ValueError("Video URL must be an S3 URL or HTTPS URL")
        return v
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v, info):
        if 'chunk_duration' in info.data and v >= info.data['chunk_duration']:
            raise ValueError("Overlap must be less than chunk duration")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "s3://videos/sample-movie.mp4",
                "user_prompt": "Identify all action scenes and track main characters throughout the video",
                "video_type": "movie",
                "chunk_duration": 15,
                "chunk_overlap": 3,
                "selected_providers": ["aws_rekognition", "nvidia_vila"]
            }
        }


class JobRetryRequest(BaseModel):
    """Request to retry a failed job"""
    force: bool = Field(default=False, description="Force retry even if max retries exceeded")
    updated_config: Optional[Dict[str, Any]] = Field(default=None, description="Updated configuration for retry")
    
    class Config:
        json_schema_extra = {
            "example": {
                "force": False,
                "updated_config": {
                    "chunk_duration": 20,
                    "selected_providers": ["aws_rekognition"]
                }
            }
        }


# Response Schemas
class VideoAnalysisResponse(BaseModel):
    """Response for video analysis request"""
    job_id: str = Field(description="Unique job identifier")
    video_id: str = Field(description="Unique video identifier")
    status: JobStatus = Field(description="Current job status")
    created_at: datetime = Field(description="Job creation timestamp")
    estimated_cost: float = Field(description="Estimated analysis cost")
    estimated_duration: float = Field(description="Estimated processing time in seconds")
    message: str = Field(description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "video_id": "video_456def",
                "status": "pending",
                "created_at": "2024-01-15T10:30:00Z",
                "estimated_cost": 12.50,
                "estimated_duration": 300.0,
                "message": "Video analysis job created successfully"
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status query"""
    job_id: str
    video_id: str
    job_type: JobType
    status: JobStatus
    progress: float = Field(ge=0, le=100)
    current_step: Optional[str] = None
    provider: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
    retry_count: int
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None
    estimated_cost: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "video_id": "video_456def",
                "job_type": "full_pipeline",
                "status": "running",
                "progress": 45.5,
                "current_step": "Processing chunk 5/10",
                "provider": "aws_rekognition",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:15Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "retry_count": 0,
                "estimated_cost": 12.50
            }
        }


class VideoAnalysisResultResponse(BaseModel):
    """Response containing video analysis results"""
    video_id: str
    video_metadata: Dict[str, Any] = Field(description="Video metadata")
    analysis_config: Dict[str, Any] = Field(description="Configuration used for analysis")
    total_scenes: int
    total_shots: int
    total_objects: int
    scenes: List[SceneDetection]
    objects: List[ObjectDetection]
    captions: List[Dict[str, Any]]
    custom_analysis: Dict[str, Any]
    provider_metadata: Dict[str, Any]
    processing_time: float
    total_cost: float
    completed_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "video_456def",
                "video_metadata": {
                    "title": "Sample Movie",
                    "duration": 120.5,
                    "fps": 30.0,
                    "resolution": "1920x1080"
                },
                "analysis_config": {
                    "chunk_duration": 15,
                    "providers": ["aws_rekognition", "nvidia_vila"]
                },
                "total_scenes": 12,
                "total_shots": 45,
                "total_objects": 234,
                "scenes": [],
                "objects": [],
                "captions": [],
                "custom_analysis": {},
                "provider_metadata": {},
                "processing_time": 300.5,
                "total_cost": 12.45,
                "completed_at": "2024-01-15T10:35:15Z"
            }
        }


class ProvidersListResponse(BaseModel):
    """Response listing available providers and their capabilities"""
    providers: List[ProviderCapability]
    total_providers: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "providers": [
                    {
                        "provider": "aws_rekognition",
                        "capabilities": ["scene_detection", "object_detection", "action_detection"],
                        "cost_per_frame": 0.001,
                        "cost_per_minute": 1.8,
                        "supports_custom_prompts": False,
                        "max_frames_per_request": 100,
                        "rate_limit_per_minute": 60
                    }
                ],
                "total_providers": 4
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid video URL format",
                "details": {"field": "video_url", "value": "invalid-url"},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


# Query Parameters
class PaginationParams(BaseModel):
    """Common pagination parameters"""
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")


class JobFilterParams(BaseModel):
    """Parameters for filtering jobs"""
    status: Optional[JobStatus] = None
    job_type: Optional[JobType] = None
    provider: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None