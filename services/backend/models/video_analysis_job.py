"""
Video analysis job model for tracking multi-provider analysis workflows.

This model tracks the overall analysis job that coordinates multiple provider-specific
processing jobs for comprehensive video analysis.
"""

from beanie import Document, Link
from pydantic import Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from .video import Video
from .processing_job import ProcessingJob


class AnalysisStatus(str, Enum):
    """Video analysis job status"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    CHUNKING = "chunking"
    ANALYZING = "analyzing"
    MERGING = "merging"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoAnalysisJob(Document):
    """
    Track overall video analysis jobs that coordinate multiple provider analyses.
    
    This is the main job that orchestrates the entire analysis pipeline including
    chunking, multi-provider analysis, result merging, knowledge graph construction,
    and embedding generation.
    """
    
    # Job identification
    processing_job_id: str  # Link to main ProcessingJob
    video_id: str
    video: Optional[Link[Video]] = None
    
    # Status tracking
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)
    progress: float = Field(ge=0, le=100, default=0)
    current_stage: Optional[str] = None
    
    # Analysis configuration
    analysis_config: Dict[str, Any] = Field(default_factory=dict)
    selected_providers: List[str] = Field(default_factory=list)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Sub-job tracking
    chunking_job_id: Optional[str] = None
    provider_job_ids: Dict[str, str] = Field(default_factory=dict)  # provider -> job_id
    knowledge_graph_job_id: Optional[str] = None
    embedding_job_id: Optional[str] = None
    
    # Results
    chunk_count: Optional[int] = None
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    merged_results: Optional[Dict[str, Any]] = None
    knowledge_graph_id: Optional[str] = None
    embedding_collection_id: Optional[str] = None
    
    # Error handling
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    failed_providers: List[str] = Field(default_factory=list)
    
    # Resource tracking
    total_cost: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "video_analysis_jobs"
        indexes = [
            [("processing_job_id", 1)],
            [("video_id", 1), ("created_at", -1)],
            [("status", 1), ("created_at", -1)],
        ]
    
    def start(self):
        """Mark analysis job as started"""
        self.status = AnalysisStatus.INITIALIZING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_stage(self, stage: AnalysisStatus, progress: float, current_stage: Optional[str] = None):
        """Update job stage and progress"""
        self.status = stage
        self.progress = min(100, max(0, progress))
        if current_stage:
            self.current_stage = current_stage
        self.updated_at = datetime.utcnow()
    
    def add_provider_job(self, provider: str, job_id: str):
        """Add a provider-specific job ID"""
        self.provider_job_ids[provider] = job_id
        self.updated_at = datetime.utcnow()
    
    def complete(self, merged_results: Optional[Dict[str, Any]] = None):
        """Mark analysis job as completed"""
        self.status = AnalysisStatus.COMPLETED
        self.progress = 100
        self.completed_at = datetime.utcnow()
        if merged_results:
            self.merged_results = merged_results
        
        # Calculate total duration
        if self.started_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        self.updated_at = datetime.utcnow()
    
    def fail(self, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Mark analysis job as failed"""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.updated_at = datetime.utcnow()
    
    def add_provider_failure(self, provider: str, error: str):
        """Record a provider-specific failure"""
        if provider not in self.failed_providers:
            self.failed_providers.append(provider)
        if not self.error_details:
            self.error_details = {}
        self.error_details[f"provider_{provider}"] = error
        self.updated_at = datetime.utcnow()
    
    def calculate_progress(self) -> float:
        """
        Calculate overall progress based on pipeline stages.
        
        Returns:
            Progress percentage (0-100)
        """
        stage_weights = {
            AnalysisStatus.PENDING: 0,
            AnalysisStatus.INITIALIZING: 5,
            AnalysisStatus.CHUNKING: 15,
            AnalysisStatus.ANALYZING: 60,
            AnalysisStatus.MERGING: 10,
            AnalysisStatus.KNOWLEDGE_GRAPH: 5,
            AnalysisStatus.EMBEDDING: 5,
            AnalysisStatus.COMPLETED: 100,
            AnalysisStatus.FAILED: self.progress,  # Keep current progress
            AnalysisStatus.CANCELLED: self.progress,  # Keep current progress
        }
        
        base_progress = stage_weights.get(self.status, 0)
        
        # Add provider-specific progress if in analyzing stage
        if self.status == AnalysisStatus.ANALYZING and self.provider_job_ids:
            # This would need to query actual provider job progress
            # For now, estimate based on number of providers
            provider_count = len(self.selected_providers)
            completed_providers = len(self.analysis_results)
            if provider_count > 0:
                provider_progress = (completed_providers / provider_count) * 60
                base_progress = 15 + provider_progress
        
        return min(100, max(0, base_progress))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get job summary for API responses"""
        return {
            "job_id": self.processing_job_id,
            "video_id": self.video_id,
            "status": self.status,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "providers": self.selected_providers,
            "failed_providers": self.failed_providers,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.total_duration_seconds,
            "error_message": self.error_message,
        }