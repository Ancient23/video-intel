"""
Video analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from beanie import PydanticObjectId
import logging

from schemas.api.video_analysis import (
    VideoAnalysisRequest,
    JobRetryRequest,
    VideoAnalysisResponse,
    JobStatusResponse,
    VideoAnalysisResultResponse,
    ProvidersListResponse,
    ErrorResponse
)
from schemas.analysis import (
    ProviderType,
    ProviderCapability,
    AnalysisGoal,
    AnalysisConfig,
    SceneDetection,
    ObjectDetection
)
from models.video import Video, VideoStatus
from models.processing_job import ProcessingJob, JobStatus, JobType
from models.scene import Scene
from services.analysis.base_analyzer import BaseAnalyzer
from services.chunking.orchestration_service import VideoChunkingOrchestrationService as OrchestrationService
from services.chunking.analysis_planner import AnalysisPlanner
from core.deps import get_current_user  # Placeholder for authentication


router = APIRouter(prefix="/video-analysis", tags=["video-analysis"])
logger = logging.getLogger(__name__)


# Provider capabilities - in production this would come from a service/config
PROVIDER_CAPABILITIES = [
    ProviderCapability(
        provider=ProviderType.AWS_REKOGNITION,
        capabilities=[
            AnalysisGoal.SCENE_DETECTION,
            AnalysisGoal.OBJECT_DETECTION,
            AnalysisGoal.ACTION_DETECTION,
            AnalysisGoal.EMOTION_ANALYSIS
        ],
        cost_per_frame=0.001,
        cost_per_minute=1.8,
        supports_custom_prompts=False,
        max_frames_per_request=100,
        rate_limit_per_minute=60
    ),
    ProviderCapability(
        provider=ProviderType.NVIDIA_VILA,
        capabilities=[
            AnalysisGoal.SCENE_DETECTION,
            AnalysisGoal.ACTION_DETECTION,
            AnalysisGoal.CHARACTER_TRACKING,
            AnalysisGoal.CUSTOM_QUERY
        ],
        cost_per_frame=0.0035,
        cost_per_minute=6.3,
        supports_custom_prompts=True,
        max_frames_per_request=50,
        rate_limit_per_minute=30
    ),
    ProviderCapability(
        provider=ProviderType.NVIDIA_COSMOS,
        capabilities=[
            AnalysisGoal.TECHNICAL_ANALYSIS,
            AnalysisGoal.CUSTOM_QUERY
        ],
        cost_per_frame=0.002,
        cost_per_minute=3.6,
        supports_custom_prompts=True,
        max_frames_per_request=100,
        rate_limit_per_minute=45
    ),
    ProviderCapability(
        provider=ProviderType.OPENAI_GPT4V,
        capabilities=[
            AnalysisGoal.SCENE_DETECTION,
            AnalysisGoal.PLOT_SUMMARY,
            AnalysisGoal.EMOTION_ANALYSIS,
            AnalysisGoal.CUSTOM_QUERY
        ],
        cost_per_frame=0.015,
        cost_per_minute=27.0,
        supports_custom_prompts=True,
        max_frames_per_request=20,
        rate_limit_per_minute=10
    ),
    ProviderCapability(
        provider=ProviderType.WHISPER,
        capabilities=[
            AnalysisGoal.DIALOGUE_EXTRACTION
        ],
        cost_per_frame=0.0,
        cost_per_minute=0.006,
        supports_custom_prompts=False,
        max_frames_per_request=0,
        rate_limit_per_minute=100
    )
]


@router.post("/analyze", response_model=VideoAnalysisResponse, status_code=status.HTTP_202_ACCEPTED,
             summary="Start video analysis",
             description="Start a new video analysis job with user prompt",
             responses={
                 202: {"description": "Analysis job created successfully"},
                 400: {"model": ErrorResponse, "description": "Invalid request"},
                 401: {"model": ErrorResponse, "description": "Authentication required"},
                 403: {"model": ErrorResponse, "description": "Insufficient permissions"}
             })
async def start_video_analysis(
    request: VideoAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)  # Placeholder
) -> VideoAnalysisResponse:
    """
    Start video analysis with natural language prompt.
    
    The system will:
    1. Parse the user prompt to determine analysis goals
    2. Select appropriate providers based on capabilities and cost
    3. Create a processing job
    4. Start the analysis pipeline asynchronously
    
    Returns job ID for tracking progress.
    """
    try:
        # Check if video already exists
        existing_video = await Video.find_one({"s3_uri": request.video_url})
        
        if existing_video:
            video = existing_video
            # Check if there's already a running job
            running_job = await ProcessingJob.find_one({
                "video_id": str(video.id),
                "status": {"$in": [JobStatus.PENDING, JobStatus.RUNNING]}
            })
            if running_job:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Video already has a running job: {running_job.id}"
                )
        else:
            # Create new video entry
            video = Video(
                title=request.video_url.split('/')[-1],  # Extract filename
                s3_uri=request.video_url,
                duration=0,  # Will be updated during processing
                fps=30.0,  # Default, will be updated
                width=1920,  # Default, will be updated
                height=1080,  # Default, will be updated
                created_by=current_user.get("user_id", "anonymous"),
                metadata=request.metadata or {}
            )
            await video.save()
        
        # Plan the analysis based on user prompt
        planner = AnalysisPlanner()
        
        # Estimate video duration if not known
        video_duration = video.duration if video.duration > 0 else 120.0  # Default 2 minutes
        
        # Analyze prompt to create config
        analysis_config = planner.analyze_prompt(
            prompt=request.user_prompt,
            video_duration_seconds=video_duration
        )
        
        # Override with any user-specified settings
        if request.chunk_duration:
            analysis_config.chunk_duration = request.chunk_duration
        if request.chunk_overlap:
            analysis_config.chunk_overlap = request.chunk_overlap
        if request.selected_providers:
            # TODO: Implement provider override logic
            pass
        
        # Apply cost limit if specified
        if request.cost_limit and analysis_config.cost_estimate > request.cost_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estimated cost ${analysis_config.cost_estimate:.2f} exceeds limit ${request.cost_limit:.2f}"
            )
        
        # Create processing job
        job = ProcessingJob(
            job_type=JobType.FULL_PIPELINE,
            video_id=str(video.id),
            video=video,
            provider="multi-provider",
            config={
                "analysis_config": analysis_config.model_dump(),
                "user_prompt": request.user_prompt,
                "cost_limit": request.cost_limit
            },
            estimated_cost=analysis_config.cost_estimate
        )
        await job.save()
        
        # Start the analysis pipeline in background
        # In production, this would trigger a Celery task
        background_tasks.add_task(
            start_analysis_pipeline,
            job_id=str(job.id),
            video_id=str(video.id),
            analysis_config=analysis_config
        )
        
        # Estimate duration based on video length and selected providers
        estimated_duration = estimate_processing_duration(
            video_duration=video.duration if video.duration > 0 else 120,  # Default 2 min
            analysis_config=analysis_config
        )
        
        return VideoAnalysisResponse(
            job_id=str(job.id),
            video_id=str(video.id),
            status=job.status,
            created_at=job.created_at,
            estimated_cost=analysis_config.cost_estimate,
            estimated_duration=estimated_duration,
            message="Video analysis job created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start video analysis: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse,
            summary="Get job status",
            description="Get the current status and progress of a processing job",
            responses={
                200: {"description": "Job status retrieved successfully"},
                404: {"model": ErrorResponse, "description": "Job not found"},
                401: {"model": ErrorResponse, "description": "Authentication required"}
            })
async def get_job_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> JobStatusResponse:
    """
    Get detailed status of a processing job.
    
    Returns current status, progress percentage, and any error information.
    """
    try:
        job = await ProcessingJob.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Create result summary if job is completed
        result_summary = None
        if job.status == JobStatus.COMPLETED and job.result:
            result_summary = {
                "total_scenes": job.result.get("total_scenes", 0),
                "total_shots": job.result.get("total_shots", 0),
                "total_objects": job.result.get("total_objects", 0),
                "providers_used": job.result.get("providers_used", []),
                "processing_time": job.get_duration()
            }
        
        return JobStatusResponse(
            job_id=str(job.id),
            video_id=job.video_id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            provider=job.provider,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at,
            retry_count=job.retry_count,
            error_message=job.error_message,
            error_details=job.error_details,
            result_summary=result_summary,
            estimated_cost=job.estimated_cost
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/videos/{video_id}/analysis", response_model=VideoAnalysisResultResponse,
            summary="Get video analysis results",
            description="Get the complete analysis results for a video",
            responses={
                200: {"description": "Analysis results retrieved successfully"},
                404: {"model": ErrorResponse, "description": "Video or results not found"},
                400: {"model": ErrorResponse, "description": "Video analysis not completed"},
                401: {"model": ErrorResponse, "description": "Authentication required"}
            })
async def get_video_analysis(
    video_id: str,
    include_scenes: bool = Query(True, description="Include scene details"),
    include_objects: bool = Query(True, description="Include object detections"),
    scene_limit: int = Query(100, ge=1, le=1000, description="Maximum scenes to return"),
    object_limit: int = Query(500, ge=1, le=5000, description="Maximum objects to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> VideoAnalysisResultResponse:
    """
    Get complete analysis results for a video.
    
    Returns all extracted knowledge including:
    - Scene boundaries and descriptions
    - Detected objects with tracking
    - Generated captions
    - Custom analysis results
    - Provider metadata
    """
    try:
        # Get video
        video = await Video.get(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video {video_id} not found"
            )
        
        # Check if analysis is completed
        if video.status != VideoStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video analysis not completed. Current status: {video.status}"
            )
        
        # Get the completed job to retrieve analysis config
        completed_job = await ProcessingJob.find_one({
            "video_id": video_id,
            "job_type": JobType.FULL_PIPELINE,
            "status": JobStatus.COMPLETED
        }).sort([("completed_at", -1)])
        
        if not completed_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No completed analysis found for this video"
            )
        
        # Get scenes
        scenes = []
        objects = []
        captions = []
        custom_analysis = {}
        provider_metadata = {}
        
        if include_scenes:
            scene_docs = await Scene.find(
                {"video_id": PydanticObjectId(video_id)}
            ).limit(scene_limit).to_list()
            
            for scene in scene_docs:
                # Convert scene data to response format
                scenes.append(SceneDetection(
                    scene_id=str(scene.id),
                    start_time=scene.start_time,
                    end_time=scene.end_time,
                    scene_type=scene.scene_type,
                    confidence=scene.confidence,
                    description=scene.description,
                    keyframe_url=scene.keyframes[0] if scene.keyframes else None,
                    provider=ProviderType.AWS_REKOGNITION  # Default for now
                ))
                
                # Aggregate objects from scene
                if include_objects and scene.visual_features:
                    for obj in scene.visual_features.get("objects", [])[:object_limit]:
                        objects.append(ObjectDetection(
                            object_id=obj.get("id", ""),
                            label=obj.get("label", ""),
                            confidence=obj.get("confidence", 0.0),
                            bounding_box=obj.get("bounding_box"),
                            frame_time=scene.start_time,  # Approximate
                            tracking_id=obj.get("tracking_id"),
                            provider=ProviderType.AWS_REKOGNITION
                        ))
                
                # Collect captions
                if scene.captions:
                    captions.extend(scene.captions)
                
                # Collect custom analysis
                if scene.custom_analysis:
                    for key, value in scene.custom_analysis.items():
                        if key not in custom_analysis:
                            custom_analysis[key] = []
                        custom_analysis[key].append(value)
        
        # Build video metadata
        video_metadata = {
            "title": video.title,
            "duration": video.duration,
            "fps": video.fps,
            "resolution": f"{video.width}x{video.height}",
            "codec": video.codec,
            "bitrate": video.bitrate,
            "created_at": video.created_at,
            "tags": video.tags
        }
        
        return VideoAnalysisResultResponse(
            video_id=video_id,
            video_metadata=video_metadata,
            analysis_config=completed_job.config.get("analysis_config", {}),
            total_scenes=video.total_scenes,
            total_shots=video.total_shots,
            total_objects=len(objects),
            scenes=scenes,
            objects=objects,
            captions=captions,
            custom_analysis=custom_analysis,
            provider_metadata=provider_metadata,
            processing_time=completed_job.get_duration() or 0.0,
            total_cost=completed_job.estimated_cost or 0.0,
            completed_at=completed_job.completed_at or datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video analysis: {str(e)}"
        )


@router.post("/jobs/{job_id}/retry", response_model=VideoAnalysisResponse,
             summary="Retry failed job",
             description="Retry a failed or cancelled job",
             responses={
                 202: {"description": "Retry started successfully"},
                 400: {"model": ErrorResponse, "description": "Job cannot be retried"},
                 404: {"model": ErrorResponse, "description": "Job not found"},
                 401: {"model": ErrorResponse, "description": "Authentication required"}
             })
async def retry_job(
    job_id: str,
    request: JobRetryRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> VideoAnalysisResponse:
    """
    Retry a failed or cancelled job.
    
    Can optionally update configuration for the retry attempt.
    """
    try:
        job = await ProcessingJob.get(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Check if job can be retried
        if job.status not in [JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job cannot be retried. Current status: {job.status}"
            )
        
        # Check retry limit unless forced
        if not request.force and job.retry_count >= job.max_retries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum retry attempts ({job.max_retries}) exceeded"
            )
        
        # Update configuration if provided
        if request.updated_config:
            job.config.update(request.updated_config)
        
        # Mark job for retry
        if not job.retry():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to mark job for retry"
            )
        
        await job.save()
        
        # Get analysis config
        analysis_config_dict = job.config.get("analysis_config", {})
        analysis_config = AnalysisConfig(**analysis_config_dict)
        
        # Start the retry in background
        background_tasks.add_task(
            start_analysis_pipeline,
            job_id=str(job.id),
            video_id=job.video_id,
            analysis_config=analysis_config,
            is_retry=True
        )
        
        return VideoAnalysisResponse(
            job_id=str(job.id),
            video_id=job.video_id,
            status=job.status,
            created_at=job.created_at,
            estimated_cost=job.estimated_cost or 0.0,
            estimated_duration=300.0,  # Default 5 minutes
            message=f"Job retry started (attempt {job.retry_count}/{job.max_retries})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry job: {str(e)}"
        )


@router.get("/providers", response_model=ProvidersListResponse,
            summary="List available providers",
            description="Get list of available analysis providers and their capabilities",
            responses={
                200: {"description": "Providers listed successfully"},
                401: {"model": ErrorResponse, "description": "Authentication required"}
            })
async def list_providers(
    capability: Optional[AnalysisGoal] = Query(None, description="Filter by capability"),
    supports_custom: Optional[bool] = Query(None, description="Filter by custom prompt support"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ProvidersListResponse:
    """
    List all available analysis providers and their capabilities.
    
    Includes:
    - Supported analysis goals
    - Cost information
    - Rate limits
    - Custom prompt support
    """
    providers = PROVIDER_CAPABILITIES.copy()
    
    # Apply filters
    if capability:
        providers = [p for p in providers if capability in p.capabilities]
    
    if supports_custom is not None:
        providers = [p for p in providers if p.supports_custom_prompts == supports_custom]
    
    return ProvidersListResponse(
        providers=providers,
        total_providers=len(providers)
    )


# Helper functions (in production these would be in separate services)

async def start_analysis_pipeline(
    job_id: str,
    video_id: str,
    analysis_config: AnalysisConfig,
    is_retry: bool = False
):
    """
    Start the video analysis pipeline.
    
    Triggers the Celery task for video processing.
    """
    from workers.video_processing import process_video_ingestion
    
    # Extract user prompt from config
    user_prompt = analysis_config.user_prompt
    
    # Trigger Celery task for ingestion
    task = process_video_ingestion.apply_async(
        args=[job_id, video_id, user_prompt],
        queue='orchestration',
        task_id=f"{job_id}-pipeline",  # Use job_id as base for task_id for tracking
        retry=True,
        retry_policy={
            'max_retries': 3,
            'interval_start': 60,  # 1 minute
            'interval_step': 120,  # 2 minutes
            'interval_max': 600,   # 10 minutes
        }
    )
    
    # Store task ID in job metadata for tracking
    try:
        job = await ProcessingJob.get(job_id)
        if job:
            job.metadata['celery_task_id'] = task.id
            job.metadata['is_retry'] = is_retry
            await job.save()
    except Exception as e:
        logger.error(f"Failed to store task ID in job: {str(e)}")
    
    logger.info(f"Started analysis pipeline task {task.id} for job {job_id}, video {video_id}")


def estimate_processing_duration(video_duration: float, analysis_config: AnalysisConfig) -> float:
    """
    Estimate processing duration based on video length and selected providers.
    
    Returns estimated duration in seconds.
    """
    # Base time: 1 second processing per 10 seconds of video
    base_time = video_duration / 10
    
    # Add overhead for each provider
    provider_overhead = len(analysis_config.selected_providers) * 30  # 30 seconds per provider
    
    # Add time for chunking and orchestration
    chunk_count = int(video_duration / analysis_config.chunk_duration)
    orchestration_time = chunk_count * 5  # 5 seconds per chunk
    
    # Total estimate with buffer
    total_time = (base_time + provider_overhead + orchestration_time) * 1.5  # 50% buffer
    
    return min(total_time, 3600)  # Cap at 1 hour