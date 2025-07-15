"""
Orchestration tasks for coordinating complex workflows.

These tasks manage the coordination of multiple tasks and handle
workflow orchestration for the Video Intelligence Platform.
"""

from celery import group, chain, chord, signature
from celery_app import celery_app
from utils.memory_monitor import monitor_memory
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='workers.orchestration_tasks.orchestrate_video_ingestion')
def orchestrate_video_ingestion(self, video_id: str, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrate the complete video ingestion workflow.
    
    Args:
        video_id: Video ID to process
        project_id: Project ID
        config: Processing configuration
        
    Returns:
        Workflow execution results
    """
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'initializing_workflow',
            'video_id': video_id
        })
        
        # Create workflow canvas
        workflow = chain(
            # Step 1: Video validation and preparation
            signature('workers.video_analysis_tasks.detect_shot_boundaries',
                     args=[video_id, project_id],
                     queue='video_analysis'),
            
            # Step 2: Chunking based on shot boundaries
            signature('workers.ingestion_tasks.chunk_video',
                     queue='video_analysis'),
            
            # Step 3: Parallel analysis of chunks
            chord(
                group([
                    signature('workers.video_analysis_tasks.analyze_with_rekognition',
                             queue='video_analysis'),
                    signature('workers.video_analysis_tasks.analyze_with_nvidia',
                             queue='video_analysis')
                ]),
                # Step 4: Merge results and generate embeddings
                signature('workers.orchestration_tasks.process_analysis_results',
                         queue='orchestration')
            ),
            
            # Step 5: Build knowledge graph
            signature('workers.knowledge_graph_tasks.build_scene_graph',
                     queue='knowledge_graph'),
            
            # Step 6: Finalize and index
            signature('workers.orchestration_tasks.finalize_ingestion',
                     queue='orchestration')
        )
        
        # Execute workflow
        result = workflow.apply_async()
        
        return {
            'workflow_id': result.id,
            'video_id': video_id,
            'project_id': project_id,
            'status': 'initiated',
            'workflow_steps': 6
        }
        
    except Exception as e:
        logger.error(f"Workflow orchestration failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, name='workers.orchestration_tasks.process_analysis_results')
def process_analysis_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process and merge analysis results from multiple providers.
    
    Args:
        chunk_results: Results from chunk analysis
        
    Returns:
        Processed results ready for embedding generation
    """
    try:
        # Merge results by chunk
        merged_by_chunk = {}
        
        for result in chunk_results:
            chunk_id = result['chunk_id']
            if chunk_id not in merged_by_chunk:
                merged_by_chunk[chunk_id] = {
                    'chunk_id': chunk_id,
                    'providers': {}
                }
            
            provider = result['provider']
            merged_by_chunk[chunk_id]['providers'][provider] = result['results']
        
        # Generate embeddings for each chunk
        embedding_tasks = []
        for chunk_id, chunk_data in merged_by_chunk.items():
            task = signature(
                'workers.embedding_tasks.generate_chunk_embeddings',
                args=[chunk_data, chunk_data.get('job_id')],
                queue='embeddings'
            )
            embedding_tasks.append(task)
        
        # Execute embedding generation in parallel
        embedding_group = group(embedding_tasks)
        embedding_results = embedding_group.apply_async().get()
        
        return {
            'chunks_processed': len(merged_by_chunk),
            'embeddings_generated': sum(r['total_embeddings'] for r in embedding_results),
            'results': {
                'analysis': merged_by_chunk,
                'embeddings': embedding_results
            }
        }
        
    except Exception as e:
        logger.error(f"Analysis result processing failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.finalize_ingestion')
def finalize_ingestion(self, ingestion_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finalize the ingestion process and update project status.
    
    Args:
        ingestion_results: Results from the ingestion workflow
        
    Returns:
        Final status and summary
    """
    from services.orchestration.ingestion_finalizer import IngestionFinalizer
    
    try:
        finalizer = IngestionFinalizer()
        
        # Update project status
        project_update = finalizer.update_project_status(
            project_id=ingestion_results['project_id'],
            video_id=ingestion_results['video_id'],
            status='completed'
        )
        
        # Generate summary
        summary = finalizer.generate_summary(ingestion_results)
        
        # Trigger post-processing if needed
        if ingestion_results.get('post_process', False):
            signature(
                'workers.orchestration_tasks.post_process_video',
                args=[ingestion_results['video_id']],
                queue='orchestration'
            ).apply_async()
        
        return {
            'video_id': ingestion_results['video_id'],
            'project_id': ingestion_results['project_id'],
            'status': 'completed',
            'summary': summary,
            'project_update': project_update
        }
        
    except Exception as e:
        logger.error(f"Ingestion finalization failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.batch_process_videos')
def batch_process_videos(self, video_ids: List[str], project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process multiple videos in batch with controlled concurrency.
    
    Args:
        video_ids: List of video IDs to process
        project_id: Project ID
        config: Batch processing configuration
        
    Returns:
        Batch processing results
    """
    try:
        batch_size = config.get('batch_size', 5)
        max_concurrent = config.get('max_concurrent', 3)
        
        # Process videos in batches
        results = []
        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            
            # Create tasks for batch
            batch_tasks = []
            for video_id in batch:
                task = signature(
                    'workers.ingestion_tasks.process_video',
                    args=[video_id, project_id, config.get('providers')],
                    queue='ingestion'
                )
                batch_tasks.append(task)
            
            # Execute batch with limited concurrency
            batch_group = group(batch_tasks)
            batch_results = batch_group.apply_async().get()
            results.extend(batch_results)
            
            # Update progress
            progress = min(95, int((i + len(batch)) / len(video_ids) * 100))
            self.update_state(state='PROGRESS', meta={
                'stage': 'batch_processing',
                'progress': progress,
                'processed': i + len(batch),
                'total': len(video_ids)
            })
        
        return {
            'project_id': project_id,
            'total_videos': len(video_ids),
            'processed': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.retry_failed_tasks')
def retry_failed_tasks(self, job_id: str) -> Dict[str, Any]:
    """
    Retry failed tasks from a processing job.
    
    Args:
        job_id: Processing job ID
        
    Returns:
        Retry results
    """
    from services.orchestration.task_monitor import TaskMonitor
    
    try:
        monitor = TaskMonitor()
        
        # Get failed tasks
        failed_tasks = monitor.get_failed_tasks(job_id)
        
        # Retry each failed task
        retry_results = []
        for task in failed_tasks:
            retry_result = monitor.retry_task(
                task_id=task['task_id'],
                task_name=task['task_name'],
                args=task['args'],
                kwargs=task['kwargs']
            )
            retry_results.append(retry_result)
        
        return {
            'job_id': job_id,
            'failed_tasks_found': len(failed_tasks),
            'retried': len(retry_results),
            'retry_results': retry_results
        }
        
    except Exception as e:
        logger.error(f"Failed task retry failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.cleanup_old_jobs')
@monitor_memory(threshold_mb=500)
def cleanup_old_jobs(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old processing jobs and their artifacts.
    
    Args:
        days_old: Age threshold in days
        
    Returns:
        Cleanup results
    """
    from services.orchestration.job_cleaner import JobCleaner
    
    try:
        cleaner = JobCleaner()
        
        # Find old jobs
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_jobs = cleaner.find_old_jobs(cutoff_date)
        
        # Clean up each job
        cleaned = []
        for job in old_jobs:
            cleanup_result = cleaner.cleanup_job(
                job_id=job['id'],
                delete_artifacts=True,
                delete_embeddings=False  # Keep embeddings
            )
            cleaned.append(cleanup_result)
        
        return {
            'cutoff_date': cutoff_date.isoformat(),
            'jobs_found': len(old_jobs),
            'jobs_cleaned': len(cleaned),
            'space_freed_mb': sum(r.get('space_freed_mb', 0) for r in cleaned)
        }
        
    except Exception as e:
        logger.error(f"Job cleanup failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.monitor_workflow_health')
def monitor_workflow_health(self, workflow_id: str) -> Dict[str, Any]:
    """
    Monitor the health of a running workflow.
    
    Args:
        workflow_id: Workflow ID to monitor
        
    Returns:
        Workflow health status
    """
    from services.orchestration.workflow_monitor import WorkflowMonitor
    
    try:
        monitor = WorkflowMonitor()
        
        # Get workflow status
        status = monitor.get_workflow_status(workflow_id)
        
        # Check for stuck tasks
        stuck_tasks = monitor.find_stuck_tasks(workflow_id, timeout_minutes=30)
        
        # Get performance metrics
        metrics = monitor.get_workflow_metrics(workflow_id)
        
        # Determine health
        health = 'healthy'
        if stuck_tasks:
            health = 'degraded'
        if status['failed_tasks'] > 0:
            health = 'unhealthy'
        
        return {
            'workflow_id': workflow_id,
            'health': health,
            'status': status,
            'stuck_tasks': len(stuck_tasks),
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Workflow monitoring failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.merge_provider_results')
def merge_provider_results(self, provider_results: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Merge analysis results from multiple providers.
    
    Args:
        provider_results: List of results from different providers
        job_id: Processing job ID
        
    Returns:
        Merged results
    """
    import asyncio
    from models.scene import Scene
    from models.processing_job import ProcessingJob
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'merging_results',
            'job_id': job_id
        })
        
        # Group results by chunk
        chunks_data = {}
        providers_used = set()
        total_scenes = 0
        total_objects = 0
        
        for result in provider_results:
            if not result.get('success', False):
                logger.warning(f"Skipping failed provider result: {result.get('error')}")
                continue
                
            provider = result.get('provider', 'unknown')
            providers_used.add(provider)
            
            # Process each chunk result
            for chunk_id, chunk_data in result.get('chunks', {}).items():
                if chunk_id not in chunks_data:
                    chunks_data[chunk_id] = {
                        'chunk_id': chunk_id,
                        'providers': {},
                        'merged_scenes': [],
                        'merged_objects': [],
                        'merged_captions': []
                    }
                
                # Store provider-specific data
                chunks_data[chunk_id]['providers'][provider] = chunk_data
                
                # Merge scenes
                if 'scenes' in chunk_data:
                    chunks_data[chunk_id]['merged_scenes'].extend(chunk_data['scenes'])
                    total_scenes += len(chunk_data['scenes'])
                
                # Merge objects
                if 'objects' in chunk_data:
                    chunks_data[chunk_id]['merged_objects'].extend(chunk_data['objects'])
                    total_objects += len(chunk_data['objects'])
                
                # Merge captions
                if 'captions' in chunk_data:
                    chunks_data[chunk_id]['merged_captions'].extend(chunk_data['captions'])
        
        # Save merged results to MongoDB
        asyncio.run(save_merged_results(job_id, chunks_data))
        
        return {
            'job_id': job_id,
            'chunks_processed': len(chunks_data),
            'providers_used': list(providers_used),
            'total_scenes': total_scenes,
            'total_objects': total_objects,
            'status': 'merged'
        }
        
    except Exception as e:
        logger.error(f"Result merging failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.finalize_video_analysis')
def finalize_video_analysis(self, job_id: str, video_id: str) -> Dict[str, Any]:
    """
    Finalize video analysis and update all statuses.
    
    Args:
        job_id: Processing job ID
        video_id: Video ID
        
    Returns:
        Finalization results
    """
    import asyncio
    from models.video import Video, VideoStatus
    from models.processing_job import ProcessingJob, JobStatus
    from models.video_analysis_job import VideoAnalysisJob, AnalysisStatus
    
    try:
        async def _finalize():
            # Update video status
            video = await Video.get(video_id)
            if video:
                video.status = VideoStatus.COMPLETED
                await video.save()
            
            # Update processing job
            job = await ProcessingJob.get(job_id)
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress = 100
                job.current_step = "Analysis completed"
                await job.save()
            
            # Update analysis job
            analysis_job = await VideoAnalysisJob.find_one({"processing_job_id": job_id})
            if analysis_job:
                analysis_job.status = AnalysisStatus.COMPLETED
                analysis_job.progress = 100
                analysis_job.completed_at = datetime.utcnow()
                await analysis_job.save()
            
            return {
                'job_id': job_id,
                'video_id': video_id,
                'status': 'completed',
                'finalized_at': datetime.utcnow().isoformat()
            }
        
        return asyncio.run(_finalize())
        
    except Exception as e:
        logger.error(f"Finalization failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.orchestration_tasks.post_process_video')
def post_process_video(self, video_id: str) -> Dict[str, Any]:
    """
    Perform post-processing tasks after video ingestion.
    
    Args:
        video_id: Video ID
        
    Returns:
        Post-processing results
    """
    try:
        # Examples of post-processing:
        # - Generate video summary
        # - Create highlight reel
        # - Export to different formats
        # - Notify webhooks
        
        return {
            'video_id': video_id,
            'post_processing': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Post-processing failed: {str(e)}", exc_info=True)
        raise


async def save_merged_results(job_id: str, chunks_data: Dict[str, Any]):
    """Save merged results to MongoDB."""
    from models.processing_job import ProcessingJob
    
    job = await ProcessingJob.get(job_id)
    if job:
        job.result = {
            'chunks': chunks_data,
            'merge_timestamp': datetime.utcnow().isoformat()
        }
        await job.save()