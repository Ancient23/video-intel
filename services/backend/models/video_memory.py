"""
Video Memory System - Core data structure for ingestion phase results

This model represents the comprehensive memory built during video ingestion,
including visual analysis, transcription, and temporal markers.
"""
from beanie import Document, Indexed
from pydantic import Field, field_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

from schemas.analysis import ProviderType


class TemporalMarkerType(str, Enum):
    """Types of temporal markers extracted during analysis"""
    SHOT_BOUNDARY = "shot_boundary"
    OBJECT_APPEARANCE = "object_appearance"
    ACTION_START = "action_start"
    ACTION_END = "action_end"
    SCENE_CHANGE = "scene_change"
    SPEAKER_CHANGE = "speaker_change"
    CUSTOM = "custom"


class TemporalMarker(Document):
    """A temporal point of interest in the video"""
    timestamp: float = Field(ge=0, description="Time in seconds from video start")
    marker_type: TemporalMarkerType
    confidence: float = Field(ge=0, le=1, default=1.0)
    description: str
    provider: ProviderType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # For object/person tracking
    tracking_id: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    
    # For scene changes
    scene_id: Optional[str] = None
    keyframe_url: Optional[str] = None


class VideoChunkMemory(Document):
    """Memory for a single video chunk"""
    chunk_id: str = Indexed(unique=True)
    chunk_index: int
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    duration: float = Field(gt=0)
    s3_uri: str
    keyframe_url: Optional[str] = None
    
    # Transcription for this chunk
    transcript_text: Optional[str] = None
    transcript_segments: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Visual analysis summary
    visual_summary: Optional[str] = None
    detected_objects: List[str] = Field(default_factory=list)
    detected_actions: List[str] = Field(default_factory=list)
    detected_scenes: List[str] = Field(default_factory=list)
    
    # Custom analysis results
    custom_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Embeddings for semantic search
    text_embedding: Optional[List[float]] = None
    visual_embedding: Optional[List[float]] = None
    multimodal_embedding: Optional[List[float]] = None
    
    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("End time must be greater than start time")
        return v


class VideoMemory(Document):
    """
    Complete memory system for a video after ingestion.
    
    This is the primary data structure that bridges the ingestion
    and runtime phases, containing all extracted knowledge.
    """
    # Video reference
    video_id: str = Indexed(unique=True)
    video_title: str
    video_duration: float = Field(gt=0)
    
    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ingestion_completed_at: Optional[datetime] = None
    processing_time_seconds: float = Field(ge=0, default=0)
    
    # Chunk information
    total_chunks: int = Field(ge=0)
    chunk_duration: int = Field(ge=5, le=60)
    chunk_overlap: int = Field(ge=0, le=10)
    chunks: List[VideoChunkMemory] = Field(default_factory=list)
    
    # Temporal markers (timestamps of interest)
    temporal_markers: List[TemporalMarker] = Field(default_factory=list)
    
    # Full transcription
    full_transcript: Optional[str] = None
    transcript_language: str = Field(default="en")
    transcript_word_count: int = Field(ge=0, default=0)
    transcript_provider: Optional[ProviderType] = None
    
    # Aggregated visual analysis
    total_objects_detected: int = Field(ge=0, default=0)
    unique_objects: List[str] = Field(default_factory=list)
    total_scenes_detected: int = Field(ge=0, default=0)
    scene_descriptions: List[str] = Field(default_factory=list)
    
    # Provider usage tracking
    providers_used: List[ProviderType] = Field(default_factory=list)
    total_cost: float = Field(ge=0, default=0)
    
    # Analysis configuration
    analysis_goals: List[str] = Field(default_factory=list)
    user_prompt: str
    custom_prompts: Dict[str, str] = Field(default_factory=dict)
    
    # Knowledge graph references
    knowledge_graph_id: Optional[str] = None
    entity_count: int = Field(ge=0, default=0)
    relationship_count: int = Field(ge=0, default=0)
    
    # Search indices
    text_search_enabled: bool = Field(default=False)
    visual_search_enabled: bool = Field(default=False)
    multimodal_search_enabled: bool = Field(default=False)
    
    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Settings:
        name = "video_memories"
        indexes = [
            [("video_id", 1)],
            [("created_at", -1)],
            [("video_title", "text")],
            [("full_transcript", "text")]
        ]
    
    @field_validator('chunks')
    @classmethod
    def validate_chunks_order(cls, v):
        """Ensure chunks are ordered by index"""
        if v:
            sorted_chunks = sorted(v, key=lambda x: x.chunk_index)
            if sorted_chunks != v:
                return sorted_chunks
        return v
    
    @field_validator('temporal_markers')
    @classmethod 
    def validate_markers_order(cls, v):
        """Ensure temporal markers are ordered by timestamp"""
        if v:
            sorted_markers = sorted(v, key=lambda x: x.timestamp)
            if sorted_markers != v:
                return sorted_markers
        return v
    
    def get_chunk_at_time(self, timestamp: float) -> Optional[VideoChunkMemory]:
        """Get the chunk that contains the given timestamp"""
        for chunk in self.chunks:
            if chunk.start_time <= timestamp <= chunk.end_time:
                return chunk
        return None
    
    def get_markers_in_range(
        self, 
        start_time: float, 
        end_time: float,
        marker_types: Optional[List[TemporalMarkerType]] = None
    ) -> List[TemporalMarker]:
        """Get all temporal markers within a time range"""
        markers = []
        for marker in self.temporal_markers:
            if start_time <= marker.timestamp <= end_time:
                if not marker_types or marker.marker_type in marker_types:
                    markers.append(marker)
        return markers
    
    def get_transcript_at_time(self, timestamp: float, context_seconds: float = 5) -> str:
        """Get transcript around a specific timestamp with context"""
        chunk = self.get_chunk_at_time(timestamp)
        if not chunk or not chunk.transcript_text:
            return ""
        
        # Find segments within context window
        start_window = max(0, timestamp - context_seconds)
        end_window = min(self.video_duration, timestamp + context_seconds)
        
        relevant_text = []
        for segment in chunk.transcript_segments:
            seg_start = segment.get('start_time', 0)
            seg_end = segment.get('end_time', 0)
            if seg_start <= end_window and seg_end >= start_window:
                relevant_text.append(segment.get('text', ''))
        
        return ' '.join(relevant_text)
    
    def to_runtime_format(self) -> Dict[str, Any]:
        """Convert to format optimized for runtime retrieval"""
        return {
            "video_id": self.video_id,
            "duration": self.video_duration,
            "chunks": [
                {
                    "id": chunk.chunk_id,
                    "start": chunk.start_time,
                    "end": chunk.end_time,
                    "transcript": chunk.transcript_text,
                    "objects": chunk.detected_objects,
                    "embedding": chunk.multimodal_embedding
                }
                for chunk in self.chunks
            ],
            "markers": [
                {
                    "time": marker.timestamp,
                    "type": marker.marker_type,
                    "description": marker.description
                }
                for marker in self.temporal_markers
            ],
            "full_transcript": self.full_transcript
        }