"""
Provider Orchestrator - Coordinates multiple analysis providers
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
import structlog

from services.analysis.base_analyzer import BaseAnalyzer
from services.analysis.providers.nvidia_vila import NvidiaVilaAnalyzer
from services.analysis.providers.aws_rekognition import AWSRekognitionAnalyzer
from schemas.analysis import (
    ChunkInfo, AnalysisConfig, AnalysisResult, ProviderType,
    SceneDetection, ObjectDetection, AnalysisGoal
)
from models import ProcessingJob, Video

logger = structlog.get_logger()


class ProviderOrchestrator:
    """Orchestrates analysis across multiple providers"""
    
    def __init__(self):
        self.providers: Dict[ProviderType, BaseAnalyzer] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        # Initialize providers based on available credentials
        try:
            self.providers[ProviderType.NVIDIA_VILA] = NvidiaVilaAnalyzer()
            logger.info("Initialized NVIDIA VILA provider")
        except Exception as e:
            logger.warning("Failed to initialize NVIDIA VILA", error=str(e))
        
        try:
            self.providers[ProviderType.AWS_REKOGNITION] = AWSRekognitionAnalyzer()
            logger.info("Initialized AWS Rekognition provider")
        except Exception as e:
            logger.warning("Failed to initialize AWS Rekognition", error=str(e))
    
    async def orchestrate_analysis(
        self,
        chunks: List[ChunkInfo],
        config: AnalysisConfig,
        video: Video,
        processing_job: Optional[ProcessingJob] = None
    ) -> List[AnalysisResult]:
        """
        Orchestrate analysis across providers for all chunks
        
        Args:
            chunks: List of video chunks to analyze
            config: Analysis configuration
            video: Video document
            processing_job: Optional job for progress tracking
            
        Returns:
            List of analysis results
        """
        all_results = []
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            if processing_job:
                progress = 50 + (40 * i / total_chunks)
                await processing_job.update_progress(
                    progress,
                    f"Analyzing chunk {i+1}/{total_chunks}"
                )
            
            # Analyze chunk with selected providers
            chunk_results = await self._analyze_chunk_with_providers(
                chunk, config, video.id
            )
            
            # Merge results from different providers
            merged_result = self._merge_provider_results(chunk_results, chunk, video.id)
            all_results.append(merged_result)
            
            # Log progress
            logger.info(
                "Chunk analysis completed",
                chunk_id=chunk.chunk_id,
                num_providers=len(chunk_results),
                total_cost=merged_result.total_cost
            )
        
        return all_results
    
    async def _analyze_chunk_with_providers(
        self,
        chunk: ChunkInfo,
        config: AnalysisConfig,
        video_id: str
    ) -> List[AnalysisResult]:
        """Analyze a single chunk with all selected providers"""
        tasks = []
        provider_types = []
        
        # Create tasks for each goal and its providers
        for goal, providers in config.selected_providers.items():
            for provider_type in providers:
                if provider_type in self.providers:
                    provider = self.providers[provider_type]
                    task = provider.analyze_chunk(chunk, config)
                    tasks.append(task)
                    provider_types.append(provider_type)
                else:
                    logger.warning(
                        f"Provider {provider_type} not available",
                        goal=goal
                    )
        
        if not tasks:
            logger.warning("No providers available for analysis")
            return []
        
        # Run all provider analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and add video_id
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Provider analysis failed",
                    provider=provider_types[i].value,
                    error=str(result)
                )
            else:
                result.video_id = video_id
                valid_results.append(result)
        
        return valid_results
    
    def _merge_provider_results(
        self,
        results: List[AnalysisResult],
        chunk: ChunkInfo,
        video_id: str
    ) -> AnalysisResult:
        """Merge results from multiple providers into a single result"""
        if not results:
            # Return empty result if no provider results
            return AnalysisResult(
                video_id=video_id,
                chunk_id=chunk.chunk_id,
                provider_metadata={"error": "No provider results available"}
            )
        
        # Start with the first result as base
        merged = AnalysisResult(
            video_id=video_id,
            chunk_id=chunk.chunk_id,
            scenes=[],
            objects=[],
            captions=[],
            custom_analysis={},
            provider_metadata={
                "providers_used": [],
                "chunk_info": {
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                    "duration": chunk.duration
                }
            },
            processing_time=0.0,
            total_cost=0.0
        )
        
        # Merge each provider's results
        for result in results:
            provider_name = result.provider_metadata.get("provider", "unknown")
            merged.provider_metadata["providers_used"].append(provider_name)
            
            # Merge scenes (avoiding duplicates)
            existing_scene_times = {(s.start_time, s.end_time) for s in merged.scenes}
            for scene in result.scenes:
                if (scene.start_time, scene.end_time) not in existing_scene_times:
                    merged.scenes.append(scene)
            
            # Merge objects
            merged.objects.extend(result.objects)
            
            # Merge captions
            merged.captions.extend(result.captions)
            
            # Merge custom analysis
            for key, value in result.custom_analysis.items():
                if key not in merged.custom_analysis:
                    merged.custom_analysis[key] = value
                else:
                    # If key exists, store under provider-specific key
                    merged.custom_analysis[f"{provider_name}_{key}"] = value
            
            # Add up costs and processing time
            merged.total_cost += result.total_cost
            merged.processing_time = max(merged.processing_time, result.processing_time)
        
        # Sort scenes by start time
        merged.scenes.sort(key=lambda s: s.start_time)
        
        # Remove duplicate objects (same label at same time)
        unique_objects = {}
        for obj in merged.objects:
            key = (obj.label, obj.frame_time)
            if key not in unique_objects or obj.confidence > unique_objects[key].confidence:
                unique_objects[key] = obj
        merged.objects = list(unique_objects.values())
        
        logger.info(
            "Merged provider results",
            chunk_id=chunk.chunk_id,
            num_providers=len(results),
            num_scenes=len(merged.scenes),
            num_objects=len(merged.objects),
            total_cost=merged.total_cost
        )
        
        return merged
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available providers"""
        available = {}
        for provider_type, provider in self.providers.items():
            available[provider_type.value] = provider.get_capabilities()
        return available
    
    async def estimate_total_cost(
        self,
        duration_seconds: float,
        config: AnalysisConfig
    ) -> float:
        """Estimate total cost across all selected providers"""
        total_cost = 0.0
        
        # Get unique providers from config
        unique_providers = set()
        for providers in config.selected_providers.values():
            unique_providers.update(providers)
        
        # Sum costs from each provider
        for provider_type in unique_providers:
            if provider_type in self.providers:
                provider = self.providers[provider_type]
                cost = provider.estimate_cost(duration_seconds, config)
                total_cost += cost
        
        return total_cost