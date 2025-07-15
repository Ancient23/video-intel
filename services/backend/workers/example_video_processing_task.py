"""
Example Celery task for video processing using the orchestration service

This shows how to integrate the orchestration service with Celery.
"""
import asyncio
from celery import shared_task, Task
from typing import Dict, Any
import structlog

from ..services.chunking import VideoChunkingOrchestrationService
from ..models import ProcessingJob, JobType, JobStatus

logger = structlog.get_logger()


class VideoProcessingTask(Task):
    """Base task with error handling and retries"""
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # 1 minute
    acks_late = True
    track_started = True


@shared_task(base=VideoProcessingTask, bind=True)
def process_video_task(
    self,
    video_id: str,
    user_prompt: str,
    processing_job_id: str = None
) -> Dict[str, Any]:
    """
    Celery task to process a video using the orchestration service
    
    Args:
        video_id: MongoDB video document ID
        user_prompt: User's analysis request
        processing_job_id: Optional processing job ID
        
    Returns:
        Processing results
    """
    logger.info(
        "Starting video processing task",
        video_id=video_id,
        task_id=self.request.id,
        job_id=processing_job_id
    )
    
    # Create orchestration service
    orchestrator = VideoChunkingOrchestrationService()
    
    # Run the async orchestration in a new event loop
    # (Celery tasks are synchronous by default)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # If no job ID provided, create one
        if not processing_job_id:
            job = ProcessingJob(
                job_type=JobType.FULL_PIPELINE,
                video_id=video_id,
                celery_task_id=self.request.id,
                config={
                    "user_prompt": user_prompt
                }
            )
            loop.run_until_complete(job.save())
            processing_job_id = str(job.id)
            logger.info("Created processing job", job_id=processing_job_id)
        
        # Run the orchestration
        result = loop.run_until_complete(
            orchestrator.process_video(
                video_id=video_id,
                user_prompt=user_prompt,
                processing_job_id=processing_job_id
            )
        )
        
        logger.info(
            "Video processing completed",
            video_id=video_id,
            chunks_processed=result["chunks_processed"],
            scenes_created=result["scenes_created"]
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Video processing failed",
            video_id=video_id,
            error=str(e),
            exc_info=True
        )
        
        # The orchestration service already updates the job status
        # Just re-raise for Celery retry mechanism
        raise
        
    finally:
        loop.close()


@shared_task(bind=True)
def process_video_batch_task(
    self,
    video_ids: list[str],
    user_prompt: str
) -> Dict[str, Any]:
    """
    Process multiple videos with the same prompt
    
    Args:
        video_ids: List of video IDs to process
        user_prompt: Analysis prompt to apply to all videos
        
    Returns:
        Summary of batch processing
    """
    from celery import group
    
    logger.info(
        "Starting batch video processing",
        num_videos=len(video_ids),
        task_id=self.request.id
    )
    
    # Create a group of tasks
    job = group(
        process_video_task.s(video_id, user_prompt)
        for video_id in video_ids
    )
    
    # Execute the group
    result = job.apply_async()
    
    # Wait for all tasks to complete
    results = result.get(disable_sync_subtasks=False)
    
    # Summarize results
    summary = {
        "total_videos": len(video_ids),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] != "success"),
        "total_chunks": sum(r.get("chunks_processed", 0) for r in results),
        "total_scenes": sum(r.get("scenes_created", 0) for r in results),
        "results": results
    }
    
    logger.info(
        "Batch processing completed",
        **summary
    )
    
    return summary


# Example usage from API endpoint:
"""
from fastapi import BackgroundTasks

@app.post("/videos/{video_id}/analyze")
async def analyze_video(
    video_id: str,
    request: AnalyzeVideoRequest,
    background_tasks: BackgroundTasks
):
    # Create processing job
    job = ProcessingJob(
        job_type=JobType.FULL_PIPELINE,
        video_id=video_id,
        config={"user_prompt": request.prompt}
    )
    await job.save()
    
    # Queue the task
    task = process_video_task.delay(
        video_id=video_id,
        user_prompt=request.prompt,
        processing_job_id=str(job.id)
    )
    
    # Update job with Celery task ID
    job.celery_task_id = task.id
    await job.save()
    
    return {
        "job_id": str(job.id),
        "task_id": task.id,
        "status": "processing"
    }
"""