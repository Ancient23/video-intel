from beanie import Document, Link
from pydantic import Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from .video import Video


class JobStatus(str, Enum):
    """Processing job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(str, Enum):
    """Types of processing jobs"""
    VIDEO_CHUNKING = "video_chunking"
    SHOT_DETECTION = "shot_detection"
    VISUAL_ANALYSIS = "visual_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    EMBEDDING_GENERATION = "embedding_generation"
    FULL_PIPELINE = "full_pipeline"


class ProcessingJob(Document):
    """Track video processing jobs"""
    
    # Job identification
    job_type: JobType
    video_id: str
    video: Optional[Link[Video]] = None
    
    # Status tracking
    status: JobStatus = Field(default=JobStatus.PENDING)
    progress: float = Field(ge=0, le=100, default=0)
    current_step: Optional[str] = None
    
    # Provider information
    provider: Optional[str] = None
    provider_job_id: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Results and errors
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Retry information
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    last_retry_at: Optional[datetime] = None
    
    # Resource usage
    cpu_seconds: Optional[float] = None
    memory_mb_peak: Optional[float] = None
    estimated_cost: Optional[float] = None
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Celery integration
    celery_task_id: Optional[str] = None
    
    class Settings:
        name = "processing_jobs"
        indexes = [
            [("video_id", 1), ("job_type", 1)],
            [("status", 1), ("created_at", -1)],
            [("celery_task_id", 1)],
        ]
    
    def start(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, progress: float, current_step: Optional[str] = None):
        """Update job progress"""
        self.progress = min(100, max(0, progress))
        if current_step:
            self.current_step = current_step
        self.updated_at = datetime.utcnow()
    
    def complete(self, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.progress = 100
        self.completed_at = datetime.utcnow()
        if result:
            self.result = result
        self.updated_at = datetime.utcnow()
    
    def fail(self, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.updated_at = datetime.utcnow()
    
    def retry(self):
        """Mark job for retry"""
        if self.retry_count >= self.max_retries:
            self.fail(f"Max retries ({self.max_retries}) exceeded")
            return False
        
        self.status = JobStatus.RETRYING
        self.retry_count += 1
        self.last_retry_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True
    
    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None