"""
Base analyzer class for all video analysis providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import structlog

from ...schemas.analysis import (
    ChunkInfo, AnalysisConfig, AnalysisResult,
    SceneDetection, ObjectDetection, ProviderType
)

logger = structlog.get_logger()


class BaseAnalyzer(ABC):
    """Abstract base class for video analysis providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.provider_type = ProviderType.CUSTOM
        
    @abstractmethod
    async def analyze_chunk(
        self,
        chunk: ChunkInfo,
        config: AnalysisConfig
    ) -> AnalysisResult:
        """
        Analyze a video chunk
        
        Args:
            chunk: Information about the chunk to analyze
            config: Analysis configuration
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities"""
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        duration_seconds: float,
        config: AnalysisConfig
    ) -> float:
        """Estimate cost for analyzing video of given duration"""
        pass
    
    def validate_chunk(self, chunk: ChunkInfo) -> bool:
        """Validate chunk has required data"""
        if not chunk.s3_uri and not chunk.local_path:
            logger.error("Chunk missing both S3 URI and local path", chunk_id=chunk.chunk_id)
            return False
        return True
    
    def create_result(
        self,
        video_id: str,
        chunk: ChunkInfo,
        processing_time: float = 0.0
    ) -> AnalysisResult:
        """Create base analysis result"""
        return AnalysisResult(
            video_id=video_id,
            chunk_id=chunk.chunk_id,
            processing_time=processing_time,
            provider_metadata={
                "provider": self.provider_type.value,
                "chunk_duration": chunk.duration,
                "time_range": {
                    "start": chunk.start_time,
                    "end": chunk.end_time
                }
            }
        )
    
    def handle_error(self, error: Exception, chunk: ChunkInfo) -> AnalysisResult:
        """Handle analysis errors gracefully"""
        logger.error(
            "Analysis failed",
            provider=self.provider_type.value,
            chunk_id=chunk.chunk_id,
            error=str(error)
        )
        
        result = self.create_result("unknown", chunk)
        result.provider_metadata["error"] = str(error)
        return result