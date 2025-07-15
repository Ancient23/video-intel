"""
Video processing tasks for the API-Celery integration.

This module contains the main task that orchestrates video analysis
when triggered from the API endpoints.
"""

from celery import group, chain, chord, signature
from celery.result import AsyncResult
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..celery_app import celery_app
from ..utils.memory_monitor import VideoProcessingTask
from ..models.processing_job import ProcessingJob, JobStatus
from ..models.video import Video, VideoStatus
from ..models.video_analysis_job import VideoAnalysisJob, AnalysisStatus
from ..schemas.analysis import AnalysisConfig, ProviderType
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    base=VideoProcessingTask,
    name='workers.video_processing.process_video_full_pipeline',
    max_retries=3,
    acks_late=True,
    track_started=True,
    task_time_limit=7200,  # 2 hours
    task_soft_time_limit=6000  # 100 minutes
)
def process_video_full_pipeline(
    self,
    job_id: str,
    video_id: str,
    analysis_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main task for processing a video through the full analysis pipeline.
    
    This task orchestrates the complete video analysis workflow:
    1. Video validation and metadata extraction
    2. Shot detection and chunking
    3. Multi-provider analysis
    4. Result merging and storage
    5. Knowledge graph construction (if enabled)
    6. Embedding generation (if enabled)
    
    Args:
        job_id: Processing job ID
        video_id: Video ID to process
        analysis_config: Analysis configuration dict
        
    Returns:
        Processing results with summary
    """
    try:
        logger.info(f"Starting full pipeline for video {video_id}, job {job_id}")
        
        # Update job status to running
        self.update_state(state='PROGRESS', meta={
            'stage': 'initializing',
            'progress': 0,
            'job_id': job_id,
            'video_id': video_id
        })
        
        # Load and validate configuration
        config = AnalysisConfig(**analysis_config)
        
        # Create workflow based on configuration
        workflow_tasks = []
        
        # Step 1: Video validation and metadata extraction
        workflow_tasks.append(
            signature(
                'workers.video_analysis_tasks.validate_and_extract_metadata',
                args=[video_id, job_id],
                queue='video_analysis'
            )
        )
        
        # Step 2: Shot detection (if scene detection is enabled)
        if any(provider.has_capability('scene_detection') for provider in config.selected_providers):
            workflow_tasks.append(
                signature(
                    'workers.video_analysis_tasks.detect_shot_boundaries',
                    args=[video_id, job_id],
                    kwargs={'config': config.model_dump()},
                    queue='video_analysis'
                )
            )
        
        # Step 3: Video chunking
        workflow_tasks.append(
            signature(
                'workers.ingestion_tasks.chunk_video',
                args=[video_id, job_id],
                kwargs={
                    'chunk_duration': config.chunk_duration,
                    'chunk_overlap': config.chunk_overlap,
                    'max_frames_per_chunk': config.max_frames_per_chunk
                },
                queue='ingestion'
            )
        )
        
        # Step 4: Multi-provider analysis (parallel)
        provider_tasks = []
        for provider_config in config.selected_providers:
            provider_type = provider_config.provider
            
            if provider_type == ProviderType.AWS_REKOGNITION:
                task_name = 'workers.video_analysis_tasks.analyze_with_rekognition'
            elif provider_type == ProviderType.NVIDIA_VILA:
                task_name = 'workers.video_analysis_tasks.analyze_with_nvidia'
            elif provider_type == ProviderType.OPENAI_GPT4V:
                task_name = 'workers.video_analysis_tasks.analyze_with_openai'
            else:
                logger.warning(f"Unsupported provider: {provider_type}")
                continue
                
            provider_tasks.append(
                signature(
                    task_name,
                    kwargs={
                        'job_id': job_id,
                        'provider_config': provider_config.model_dump()
                    },
                    queue='video_analysis'
                )
            )
        
        # Create chord for parallel provider analysis with result merging
        if provider_tasks:
            workflow_tasks.append(
                chord(
                    group(provider_tasks),
                    signature(
                        'workers.orchestration_tasks.merge_provider_results',
                        args=[job_id],
                        queue='orchestration'
                    )
                )
            )
        
        # Step 5: Knowledge graph construction (if enabled)
        if config.enable_knowledge_graph:
            workflow_tasks.append(
                signature(
                    'workers.knowledge_graph_tasks.build_video_knowledge_graph',
                    args=[video_id, job_id],
                    queue='knowledge_graph'
                )
            )
        
        # Step 6: Embedding generation (if enabled)
        if config.enable_embeddings:
            workflow_tasks.append(
                signature(
                    'workers.embedding_tasks.generate_video_embeddings',
                    args=[video_id, job_id],
                    queue='embeddings'
                )
            )
        
        # Step 7: Finalization
        workflow_tasks.append(
            signature(
                'workers.orchestration_tasks.finalize_video_analysis',
                args=[job_id, video_id],
                queue='orchestration'
            )
        )
        
        # Create and execute workflow chain
        workflow = chain(*workflow_tasks)
        result = workflow.apply_async()
        
        # Store workflow ID in job for tracking
        asyncio.run(update_job_workflow_id(job_id, result.id))
        
        # Monitor workflow progress
        return monitor_workflow_progress(self, result, job_id, video_id)
        
    except Exception as e:
        logger.error(f"Pipeline failed for video {video_id}: {str(e)}", exc_info=True)
        
        # Update job status to failed
        asyncio.run(update_job_status(job_id, JobStatus.FAILED, str(e)))
        
        # Retry if within limits
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            raise


@celery_app.task(
    bind=True,
    name='workers.video_processing.update_job_progress',
    acks_late=True
)
def update_job_progress(
    self,
    job_id: str,
    progress: int,
    current_step: str,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update job progress in MongoDB.
    
    Args:
        job_id: Processing job ID
        progress: Progress percentage (0-100)
        current_step: Current processing step description
        meta: Additional metadata
        
    Returns:
        Update result
    """
    import asyncio
    
    try:
        async def _update():
            # Update ProcessingJob
            job = await ProcessingJob.get(job_id)
            if job:
                job.progress = progress
                job.current_step = current_step
                if meta:
                    job.metadata.update(meta)
                await job.save()
                
            # Update VideoAnalysisJob if exists
            analysis_job = await VideoAnalysisJob.find_one({"processing_job_id": job_id})
            if analysis_job:
                analysis_job.progress = progress
                analysis_job.current_stage = current_step
                if meta:
                    analysis_job.metadata.update(meta)
                await analysis_job.save()
                
            return {
                'job_id': job_id,
                'progress': progress,
                'current_step': current_step,
                'updated': True
            }
            
        return asyncio.run(_update())
        
    except Exception as e:
        logger.error(f"Failed to update job progress: {str(e)}", exc_info=True)
        return {
            'job_id': job_id,
            'progress': progress,
            'updated': False,
            'error': str(e)
        }


# Helper functions

def monitor_workflow_progress(task_instance, workflow_result: AsyncResult, job_id: str, video_id: str) -> Dict[str, Any]:
    """
    Monitor workflow progress and update job status.
    """
    import time
    import asyncio
    
    start_time = time.time()
    last_progress = 0
    
    while not workflow_result.ready():
        # Get current task info
        current_task = workflow_result.current_task_name() or "processing"
        
        # Calculate progress based on workflow position
        if workflow_result.info:
            progress = workflow_result.info.get('progress', last_progress)
        else:
            # Estimate progress based on time
            elapsed = time.time() - start_time
            progress = min(95, int(elapsed / 300 * 100))  # Assume 5 min total
            
        if progress > last_progress:
            last_progress = progress
            
            # Update task state
            task_instance.update_state(
                state='PROGRESS',
                meta={
                    'stage': current_task,
                    'progress': progress,
                    'job_id': job_id,
                    'video_id': video_id
                }
            )
            
            # Update job in MongoDB
            update_job_progress.apply_async(
                args=[job_id, progress, current_task],
                queue='orchestration'
            )
        
        time.sleep(5)  # Check every 5 seconds
    
    # Get final result
    if workflow_result.successful():
        result = workflow_result.result
        asyncio.run(update_job_status(job_id, JobStatus.COMPLETED))
        return {
            'status': 'completed',
            'job_id': job_id,
            'video_id': video_id,
            'result': result,
            'duration': time.time() - start_time
        }
    else:
        error = str(workflow_result.info)
        asyncio.run(update_job_status(job_id, JobStatus.FAILED, error))
        return {
            'status': 'failed',
            'job_id': job_id,
            'video_id': video_id,
            'error': error,
            'duration': time.time() - start_time
        }


async def update_job_status(job_id: str, status: JobStatus, error: Optional[str] = None):
    """Update job status in MongoDB."""
    job = await ProcessingJob.get(job_id)
    if job:
        job.status = status
        if error:
            job.error_message = error
        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()
        await job.save()
        
    # Also update VideoAnalysisJob
    analysis_job = await VideoAnalysisJob.find_one({"processing_job_id": job_id})
    if analysis_job:
        if status == JobStatus.COMPLETED:
            analysis_job.status = AnalysisStatus.COMPLETED
        elif status == JobStatus.FAILED:
            analysis_job.status = AnalysisStatus.FAILED
        analysis_job.error_message = error
        await analysis_job.save()


async def update_job_workflow_id(job_id: str, workflow_id: str):
    """Store workflow ID in job for tracking."""
    job = await ProcessingJob.get(job_id)
    if job:
        job.metadata['workflow_id'] = workflow_id
        await job.save()


import asyncio