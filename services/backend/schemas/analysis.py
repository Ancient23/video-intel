"""
Analysis configuration schemas for video processing
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from enum import Enum


class VideoType(str, Enum):
    """Types of video content"""
    MOVIE = "movie"
    DOCUMENTARY = "documentary"
    TUTORIAL = "tutorial"
    SPORTS = "sports"
    NEWS = "news"
    SURVEILLANCE = "surveillance"
    GENERAL = "general"


class AnalysisGoal(str, Enum):
    """Analysis goals that can be extracted from user prompts"""
    SCENE_DETECTION = "scene_detection"
    ACTION_DETECTION = "action_detection"
    CHARACTER_TRACKING = "character_tracking"
    OBJECT_DETECTION = "object_detection"
    DIALOGUE_EXTRACTION = "dialogue_extraction"
    EMOTION_ANALYSIS = "emotion_analysis"
    PLOT_SUMMARY = "plot_summary"
    TECHNICAL_ANALYSIS = "technical_analysis"
    CUSTOM_QUERY = "custom_query"


class ProviderType(str, Enum):
    """Available analysis providers"""
    AWS_REKOGNITION = "aws_rekognition"
    NVIDIA_VILA = "nvidia_vila"
    NVIDIA_COSMOS = "nvidia_cosmos"
    OPENAI_GPT4V = "openai_gpt4v"
    WHISPER = "whisper"
    CUSTOM = "custom"


class ChunkInfo(BaseModel):
    """Information about a video chunk"""
    chunk_id: str
    chunk_index: int
    start_time: float = Field(ge=0)
    end_time: float = Field(gt=0)
    duration: float = Field(gt=0)
    local_path: Optional[str] = None
    s3_uri: Optional[str] = None
    keyframe_path: Optional[str] = None
    
    @field_validator('end_time')
    @classmethod
    def validate_time_range(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("End time must be greater than start time")
        return v


class AnalysisConfig(BaseModel):
    """Configuration for video analysis based on user prompt"""
    user_prompt: str
    video_type: VideoType = VideoType.GENERAL
    analysis_goals: List[AnalysisGoal] = Field(default_factory=list)
    selected_providers: Dict[str, List[ProviderType]] = Field(default_factory=dict)
    chunk_duration: int = Field(default=10, ge=5, le=60)
    chunk_overlap: int = Field(default=2, ge=0, le=10)
    cost_estimate: float = Field(default=0.0, ge=0)
    max_frames_per_chunk: int = Field(default=30)
    custom_prompts: Dict[str, str] = Field(default_factory=dict)
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v, info):
        if 'chunk_duration' in info.data and v >= info.data['chunk_duration']:
            raise ValueError("Overlap must be less than chunk duration")
        return v


class ProviderCapability(BaseModel):
    """Describes what a provider can do"""
    provider: ProviderType
    capabilities: List[AnalysisGoal]
    cost_per_frame: float
    cost_per_minute: float
    supports_custom_prompts: bool = False
    max_frames_per_request: int = 100
    rate_limit_per_minute: Optional[int] = None


class SceneDetection(BaseModel):
    """Scene detection result"""
    scene_id: str
    start_time: float
    end_time: float
    scene_type: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    description: Optional[str] = None
    keyframe_url: Optional[str] = None
    provider: ProviderType


class ObjectDetection(BaseModel):
    """Object detection result"""
    object_id: str
    label: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: Optional[Dict[str, float]] = None
    frame_time: float
    tracking_id: Optional[str] = None
    provider: ProviderType


class AnalysisResult(BaseModel):
    """Combined analysis results from all providers"""
    video_id: str
    chunk_id: str
    scenes: List[SceneDetection] = Field(default_factory=list)
    objects: List[ObjectDetection] = Field(default_factory=list)
    captions: List[Dict[str, Any]] = Field(default_factory=list)
    custom_analysis: Dict[str, Any] = Field(default_factory=dict)
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float = 0.0
    total_cost: float = 0.0