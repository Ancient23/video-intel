"""
Video Chunking Orchestration Service

Main entry point for video processing that coordinates:
1. Video chunking
2. Analysis planning
3. Provider orchestration
4. MongoDB updates
5. S3 artifact management
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog
from beanie import PydanticObjectId

from ...models import Video, VideoStatus, Scene, ProcessingJob, JobStatus, JobType
from ...schemas.analysis import (
    AnalysisConfig, ChunkInfo, AnalysisResult,
    SceneDetection, AnalysisGoal
)
from .video_chunker import VideoChunker
from .analysis_planner import AnalysisPlanner
from .provider_orchestrator import ProviderOrchestrator

logger = structlog.get_logger()


class VideoChunkingOrchestrationService:
    """
    Main orchestration service for video chunking and analysis.
    This is the primary entry point for Celery tasks.
    """
    
    def __init__(
        self,
        s3_client=None,
        temp_dir: Optional[str] = None,
        s3_output_bucket: Optional[str] = None
    ):
        """
        Initialize the orchestration service
        
        Args:
            s3_client: Optional S3 client instance
            temp_dir: Optional temporary directory for processing
            s3_output_bucket: Optional S3 bucket for outputs (defaults to env var)
        """
        self.video_chunker = VideoChunker(s3_client=s3_client, temp_dir=temp_dir)
        self.analysis_planner = AnalysisPlanner()
        self.provider_orchestrator = ProviderOrchestrator()
        self.s3_output_bucket = s3_output_bucket or os.getenv('S3_OUTPUT_BUCKET')
        
        if not self.s3_output_bucket:
            logger.warning("S3_OUTPUT_BUCKET not configured, will use source bucket")
    
    async def process_video(
        self,
        video_id: str,
        user_prompt: str,
        processing_job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing a video
        
        Args:
            video_id: MongoDB video document ID
            user_prompt: User's analysis request
            processing_job_id: Optional processing job ID for tracking
            
        Returns:
            Dict with processing results and statistics
        """
        job = None
        video = None
        
        try:
            # Load video and job documents
            video = await Video.get(video_id)
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            if processing_job_id:
                job = await ProcessingJob.get(processing_job_id)
                if job:
                    await job.start()
                    await job.save()
            
            logger.info(
                "Starting video processing",
                video_id=video_id,
                video_name=video.filename,
                duration=video.duration
            )
            
            # Update video status
            video.status = VideoStatus.PROCESSING
            video.processing_started_at = datetime.utcnow()
            await video.save()
            
            # Step 1: Create analysis plan
            if job:
                await job.update_progress(5, "Creating analysis plan")
                await job.save()
            
            analysis_config = self.analysis_planner.analyze_prompt(
                user_prompt,
                video.duration
            )
            
            logger.info(
                "Analysis plan created",
                goals=analysis_config.analysis_goals,
                providers=list(set(
                    p for providers in analysis_config.selected_providers.values() 
                    for p in providers
                )),
                cost_estimate=analysis_config.cost_estimate
            )
            
            # Save analysis config to video
            video.analysis_config = analysis_config.model_dump()
            await video.save()
            
            # Step 2: Chunk video
            if job:
                await job.update_progress(10, "Chunking video")
                await job.save()
            
            chunks = await self._chunk_video(video, analysis_config, job)
            
            logger.info(
                "Video chunking completed",
                num_chunks=len(chunks),
                total_duration=video.duration
            )
            
            # Step 3: Analyze chunks with providers
            if job:
                await job.update_progress(50, "Analyzing video chunks")
                await job.save()
            
            analysis_results = await self.provider_orchestrator.orchestrate_analysis(
                chunks,
                analysis_config,
                video,
                job
            )
            
            # Step 4: Create scenes from analysis results
            if job:
                await job.update_progress(90, "Creating scene documents")
                await job.save()
            
            scenes = await self._create_scenes(video, analysis_results, chunks)
            
            # Step 5: Update video document
            video.status = VideoStatus.ANALYZED
            video.processing_completed_at = datetime.utcnow()
            video.total_scenes = len(scenes)
            video.analysis_metadata = {
                "total_chunks": len(chunks),
                "total_objects_detected": sum(len(r.objects) for r in analysis_results),
                "providers_used": list(set(
                    p for providers in analysis_config.selected_providers.values() 
                    for p in providers
                )),
                "total_cost": sum(r.total_cost for r in analysis_results),
                "user_prompt": user_prompt
            }
            await video.save()
            
            # Complete the job
            if job:
                await job.complete({
                    "video_id": str(video.id),
                    "chunks_processed": len(chunks),
                    "scenes_created": len(scenes),
                    "total_cost": video.analysis_metadata["total_cost"],
                    "duration_seconds": (
                        video.processing_completed_at - video.processing_started_at
                    ).total_seconds()
                })
                await job.save()
            
            # Cleanup temporary files
            self.video_chunker.cleanup()
            
            result = {
                "status": "success",
                "video_id": str(video.id),
                "chunks_processed": len(chunks),
                "scenes_created": len(scenes),
                "total_cost": video.analysis_metadata["total_cost"],
                "processing_time": (
                    video.processing_completed_at - video.processing_started_at
                ).total_seconds(),
                "analysis_config": analysis_config.model_dump()
            }
            
            logger.info(
                "Video processing completed successfully",
                **result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Video processing failed",
                video_id=video_id,
                error=str(e),
                exc_info=True
            )
            
            # Update video status
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = str(e)
                await video.save()
            
            # Fail the job
            if job:
                await job.fail(
                    str(e),
                    {"exception_type": type(e).__name__}
                )
                await job.save()
            
            # Cleanup
            self.video_chunker.cleanup()
            
            raise
    
    async def _chunk_video(
        self,
        video: Video,
        config: AnalysisConfig,
        job: Optional[ProcessingJob] = None
    ) -> List[ChunkInfo]:
        """
        Chunk video using the video chunker service
        
        The VideoChunker is synchronous, so we run it in a thread pool
        to avoid blocking the event loop.
        """
        # Run the synchronous video chunking in a thread pool
        loop = asyncio.get_event_loop()
        
        # The video chunker will update the job object directly
        # We'll save it periodically
        chunks = await loop.run_in_executor(
            None,
            self.video_chunker.process_video,
            video.s3_uri,
            config,
            job
        )
        
        # Save the job after chunking completes
        if job:
            await job.save()
        
        # Save chunk information to video
        video.chunks = [
            {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "duration": chunk.duration,
                "s3_uri": chunk.s3_uri,
                "keyframe_url": chunk.keyframe_path
            }
            for chunk in chunks
        ]
        await video.save()
        
        return chunks
    
    async def _create_scenes(
        self,
        video: Video,
        analysis_results: List[AnalysisResult],
        chunks: List[ChunkInfo]
    ) -> List[Scene]:
        """Create Scene documents from analysis results"""
        scenes = []
        scene_index = 0
        
        # Group analysis results by detected scenes
        all_scene_detections = []
        for result in analysis_results:
            all_scene_detections.extend(result.scenes)
        
        # Sort by start time
        all_scene_detections.sort(key=lambda s: s.start_time)
        
        # Merge overlapping scenes
        merged_scenes = self._merge_overlapping_scenes(all_scene_detections)
        
        # Create Scene documents
        for scene_detection in merged_scenes:
            # Find which chunks this scene spans
            scene_chunks = []
            for chunk in chunks:
                if (chunk.start_time <= scene_detection.end_time and 
                    chunk.end_time >= scene_detection.start_time):
                    scene_chunks.append(chunk.chunk_id)
            
            # Get analysis data for this scene
            scene_analysis = self._extract_scene_analysis(
                scene_detection,
                analysis_results,
                chunks
            )
            
            scene = Scene(
                video_id=str(video.id),
                scene_index=scene_index,
                start_time=scene_detection.start_time,
                end_time=scene_detection.end_time,
                duration=scene_detection.end_time - scene_detection.start_time,
                scene_type=scene_detection.scene_type,
                description=scene_detection.description,
                keyframe_url=scene_detection.keyframe_url,
                chunk_ids=scene_chunks,
                analysis_data=scene_analysis,
                confidence_score=scene_detection.confidence
            )
            
            await scene.save()
            scenes.append(scene)
            scene_index += 1
        
        # If no scenes were detected, create one scene for the entire video
        if not scenes:
            logger.warning("No scenes detected, creating single scene for entire video")
            
            scene = Scene(
                video_id=str(video.id),
                scene_index=0,
                start_time=0.0,
                end_time=video.duration,
                duration=video.duration,
                scene_type="full_video",
                description="Complete video (no scene breaks detected)",
                chunk_ids=[chunk.chunk_id for chunk in chunks],
                analysis_data={
                    "objects": self._collect_all_objects(analysis_results),
                    "captions": self._collect_all_captions(analysis_results),
                    "custom_analysis": self._merge_custom_analysis(analysis_results)
                }
            )
            
            await scene.save()
            scenes.append(scene)
        
        logger.info(
            "Created scene documents",
            num_scenes=len(scenes),
            video_id=str(video.id)
        )
        
        return scenes
    
    def _merge_overlapping_scenes(
        self,
        scene_detections: List[SceneDetection]
    ) -> List[SceneDetection]:
        """Merge overlapping scene detections from different providers"""
        if not scene_detections:
            return []
        
        merged = []
        current = scene_detections[0]
        
        for scene in scene_detections[1:]:
            # If scenes overlap or are very close (within 1 second)
            if scene.start_time <= current.end_time + 1.0:
                # Extend the current scene
                current = SceneDetection(
                    scene_id=f"{current.scene_id}_{scene.scene_id}",
                    start_time=current.start_time,
                    end_time=max(current.end_time, scene.end_time),
                    scene_type=current.scene_type or scene.scene_type,
                    confidence=max(current.confidence, scene.confidence),
                    description=self._merge_descriptions(
                        current.description,
                        scene.description
                    ),
                    keyframe_url=current.keyframe_url or scene.keyframe_url,
                    provider=current.provider
                )
            else:
                # No overlap, add current and start new
                merged.append(current)
                current = scene
        
        # Add the last scene
        merged.append(current)
        
        return merged
    
    def _merge_descriptions(self, desc1: Optional[str], desc2: Optional[str]) -> Optional[str]:
        """Merge two scene descriptions"""
        if not desc1:
            return desc2
        if not desc2:
            return desc1
        if desc1 == desc2:
            return desc1
        return f"{desc1}. {desc2}"
    
    def _extract_scene_analysis(
        self,
        scene: SceneDetection,
        analysis_results: List[AnalysisResult],
        chunks: List[ChunkInfo]
    ) -> Dict[str, Any]:
        """Extract analysis data relevant to a specific scene"""
        scene_data = {
            "objects": [],
            "captions": [],
            "custom_analysis": {},
            "providers": []
        }
        
        # Find all analysis results that overlap with this scene
        for result in analysis_results:
            # Find the chunk for this result
            chunk = next((c for c in chunks if c.chunk_id == result.chunk_id), None)
            if not chunk:
                continue
            
            # Check if chunk overlaps with scene
            if (chunk.start_time <= scene.end_time and 
                chunk.end_time >= scene.start_time):
                
                # Add objects that fall within the scene time range
                for obj in result.objects:
                    absolute_time = chunk.start_time + obj.frame_time
                    if scene.start_time <= absolute_time <= scene.end_time:
                        scene_data["objects"].append(obj.model_dump())
                
                # Add captions
                scene_data["captions"].extend(result.captions)
                
                # Merge custom analysis
                for key, value in result.custom_analysis.items():
                    if key not in scene_data["custom_analysis"]:
                        scene_data["custom_analysis"][key] = []
                    scene_data["custom_analysis"][key].append(value)
                
                # Track providers used
                if result.provider_metadata.get("providers_used"):
                    scene_data["providers"].extend(
                        result.provider_metadata["providers_used"]
                    )
        
        # Deduplicate providers
        scene_data["providers"] = list(set(scene_data["providers"]))
        
        return scene_data
    
    def _collect_all_objects(self, analysis_results: List[AnalysisResult]) -> List[Dict]:
        """Collect all detected objects from analysis results"""
        objects = []
        for result in analysis_results:
            objects.extend([obj.model_dump() for obj in result.objects])
        return objects
    
    def _collect_all_captions(self, analysis_results: List[AnalysisResult]) -> List[Dict]:
        """Collect all captions from analysis results"""
        captions = []
        for result in analysis_results:
            captions.extend(result.captions)
        return captions
    
    def _merge_custom_analysis(
        self,
        analysis_results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """Merge custom analysis from all results"""
        merged = {}
        for result in analysis_results:
            for key, value in result.custom_analysis.items():
                if key not in merged:
                    merged[key] = []
                merged[key].append(value)
        return merged
    
    async def retry_failed_job(self, job_id: str) -> Dict[str, Any]:
        """Retry a failed processing job"""
        job = await ProcessingJob.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != JobStatus.FAILED:
            raise ValueError(f"Job {job_id} is not in failed state")
        
        # Check retry limit
        if not job.retry():
            await job.save()
            raise ValueError(f"Job {job_id} has exceeded max retries")
        
        await job.save()
        
        # Get the video
        video = await Video.get(job.video_id)
        if not video:
            raise ValueError(f"Video {job.video_id} not found")
        
        # Extract user prompt from config or video
        user_prompt = job.config.get("user_prompt")
        if not user_prompt and video.analysis_config:
            user_prompt = video.analysis_config.get("user_prompt")
        
        if not user_prompt:
            raise ValueError("Cannot retry job: user prompt not found")
        
        # Retry the processing
        return await self.process_video(
            job.video_id,
            user_prompt,
            str(job.id)
        )
    
    async def get_processing_status(self, video_id: str) -> Dict[str, Any]:
        """Get the current processing status of a video"""
        video = await Video.get(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        # Find active jobs
        jobs = await ProcessingJob.find(
            ProcessingJob.video_id == video_id,
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
        ).to_list()
        
        active_job = jobs[0] if jobs else None
        
        return {
            "video_id": str(video.id),
            "status": video.status,
            "progress": active_job.progress if active_job else 0,
            "current_step": active_job.current_step if active_job else None,
            "total_scenes": video.total_scenes,
            "processing_started_at": video.processing_started_at,
            "processing_completed_at": video.processing_completed_at,
            "error_message": video.error_message,
            "active_job_id": str(active_job.id) if active_job else None
        }