"""
Ingestion phase tasks for Video Intelligence Platform.

These tasks handle the heavy preprocessing phase where videos are analyzed
and knowledge is extracted and stored.
"""

from celery import group, chain, chord
from celery_app import celery_app
from utils.memory_monitor import VideoProcessingTask, monitor_memory
from services.chunking.orchestration_service import OrchestrationService
from services.analysis.providers.aws_rekognition import AWSRekognitionProvider
from services.analysis.providers.nvidia_vila import NvidiaVilaProvider
from models.video import Video
from models.processing_job import ProcessingJob
from core.database import get_async_session
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=VideoProcessingTask, name='workers.ingestion_tasks.process_video')
def process_video(self, video_id: str, project_id: str, provider_names: list[str] = None):
    """
    Main video processing task that orchestrates the entire ingestion pipeline.
    
    Args:
        video_id: ID of the video to process
        project_id: ID of the project
        provider_names: List of provider names to use (default: all available)
    
    Returns:
        Dict with processing results
    """
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'stage': 'initializing', 'progress': 0})
        
        # Initialize orchestration service
        orchestration_service = OrchestrationService()
        
        # Create processing job
        job_id = orchestration_service.create_processing_job(
            video_id=video_id,
            project_id=project_id,
            provider_names=provider_names
        )
        
        # Update state
        self.update_state(state='PROGRESS', meta={
            'stage': 'chunking',
            'progress': 10,
            'job_id': str(job_id)
        })
        
        # Phase 1: Video chunking
        chunking_result = chunk_video.apply_async(
            args=[video_id, job_id],
            queue='video_analysis'
        ).get()
        
        # Update state
        self.update_state(state='PROGRESS', meta={
            'stage': 'analyzing',
            'progress': 30,
            'chunks': len(chunking_result['chunks'])
        })
        
        # Phase 2: Parallel analysis of chunks
        analysis_tasks = []
        for chunk in chunking_result['chunks']:
            for provider in provider_names or ['aws_rekognition']:
                task = analyze_chunk.signature(
                    args=[chunk['id'], provider, job_id],
                    queue='video_analysis'
                )
                analysis_tasks.append(task)
        
        # Execute analysis in parallel
        analysis_group = group(analysis_tasks)
        analysis_results = analysis_group.apply_async().get()
        
        # Update state
        self.update_state(state='PROGRESS', meta={
            'stage': 'embeddings',
            'progress': 60
        })
        
        # Phase 3: Generate embeddings
        embedding_task = generate_embeddings.apply_async(
            args=[job_id, analysis_results],
            queue='embeddings'
        )
        embedding_results = embedding_task.get()
        
        # Update state
        self.update_state(state='PROGRESS', meta={
            'stage': 'knowledge_graph',
            'progress': 80
        })
        
        # Phase 4: Build knowledge graph
        graph_task = build_knowledge_graph.apply_async(
            args=[job_id, analysis_results, embedding_results],
            queue='knowledge_graph'
        )
        graph_results = graph_task.get()
        
        # Final update
        self.update_state(state='PROGRESS', meta={
            'stage': 'finalizing',
            'progress': 95
        })
        
        # Finalize job
        final_results = orchestration_service.finalize_job(
            job_id=job_id,
            results={
                'chunks': chunking_result,
                'analysis': analysis_results,
                'embeddings': embedding_results,
                'knowledge_graph': graph_results
            }
        )
        
        return {
            'job_id': str(job_id),
            'video_id': video_id,
            'project_id': project_id,
            'status': 'completed',
            'results': final_results
        }
        
    except Exception as e:
        logger.error(f"Video processing failed for {video_id}: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, name='workers.ingestion_tasks.chunk_video')
@monitor_memory(task_type='video_processing')
def chunk_video(self, video_id: str, job_id: str):
    """
    Chunk video into analyzable segments.
    
    Args:
        video_id: ID of the video
        job_id: Processing job ID
        
    Returns:
        Dict with chunk information
    """
    from services.chunking.video_chunker import VideoChunker
    
    try:
        chunker = VideoChunker()
        chunks = chunker.chunk_video(video_id, job_id)
        
        return {
            'video_id': video_id,
            'chunks': [chunk.model_dump() for chunk in chunks],
            'total_chunks': len(chunks)
        }
    except Exception as e:
        logger.error(f"Video chunking failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.ingestion_tasks.analyze_chunk')
@monitor_memory(task_type='video_processing')
def analyze_chunk(self, chunk_id: str, provider_name: str, job_id: str):
    """
    Analyze a video chunk with specified provider.
    
    Args:
        chunk_id: ID of the chunk
        provider_name: Name of the analysis provider
        job_id: Processing job ID
        
    Returns:
        Analysis results
    """
    from services.analysis.factory import ProviderFactory
    
    try:
        provider = ProviderFactory.create_provider(provider_name)
        results = provider.analyze_chunk(chunk_id, job_id)
        
        return {
            'chunk_id': chunk_id,
            'provider': provider_name,
            'results': results
        }
    except Exception as e:
        logger.error(f"Chunk analysis failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.ingestion_tasks.generate_embeddings')
@monitor_memory(task_type='embedding_generation')
def generate_embeddings(self, job_id: str, analysis_results: list):
    """
    Generate embeddings from analysis results.
    
    Args:
        job_id: Processing job ID
        analysis_results: Results from chunk analysis
        
    Returns:
        Embedding results
    """
    from services.embeddings.embedding_service import EmbeddingService
    
    try:
        embedding_service = EmbeddingService()
        embeddings = embedding_service.generate_embeddings(job_id, analysis_results)
        
        return {
            'job_id': job_id,
            'total_embeddings': len(embeddings),
            'embedding_ids': [str(e.id) for e in embeddings]
        }
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.ingestion_tasks.build_knowledge_graph')
@monitor_memory(task_type='knowledge_graph')
def build_knowledge_graph(self, job_id: str, analysis_results: list, embedding_results: dict):
    """
    Build knowledge graph from analysis and embedding results.
    
    Args:
        job_id: Processing job ID
        analysis_results: Results from chunk analysis
        embedding_results: Results from embedding generation
        
    Returns:
        Knowledge graph construction results
    """
    from services.knowledge_graph.graph_builder import GraphBuilder
    
    try:
        graph_builder = GraphBuilder()
        graph = graph_builder.build_graph(job_id, analysis_results, embedding_results)
        
        return {
            'job_id': job_id,
            'nodes_created': graph['nodes_created'],
            'edges_created': graph['edges_created'],
            'graph_id': graph['graph_id']
        }
    except Exception as e:
        logger.error(f"Knowledge graph construction failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.ingestion_tasks.reprocess_failed_chunks')
def reprocess_failed_chunks(self, job_id: str):
    """
    Reprocess any failed chunks from a job.
    
    Args:
        job_id: Processing job ID
        
    Returns:
        Reprocessing results
    """
    # Implementation for reprocessing failed chunks
    pass