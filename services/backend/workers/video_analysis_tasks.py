"""
Video analysis tasks for different providers.

These tasks handle the actual video analysis using various AI providers
like AWS Rekognition, NVIDIA VILA, etc.
"""

from celery import Task
from celery_app import celery_app
from utils.memory_monitor import VideoProcessingTask, monitor_memory
from services.analysis.providers.aws_rekognition import AWSRekognitionProvider
from services.analysis.providers.nvidia_vila import NvidiaVilaProvider
from core.database import get_async_session
from utils.cache import cache_result, get_cached_result
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=VideoProcessingTask, name='workers.video_analysis_tasks.analyze_with_rekognition')
def analyze_with_rekognition(self, video_path: str, chunk_info: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Analyze video chunk with AWS Rekognition.
    
    Args:
        video_path: S3 path to video chunk
        chunk_info: Chunk metadata (start_time, end_time, etc.)
        job_id: Processing job ID
        
    Returns:
        Analysis results from Rekognition
    """
    try:
        # Check cache first
        cache_key = f"rekognition:{job_id}:{chunk_info['chunk_id']}"
        cached = get_cached_result(cache_key)
        if cached:
            logger.info(f"Using cached Rekognition results for chunk {chunk_info['chunk_id']}")
            return cached
        
        # Update state
        self.update_state(state='PROGRESS', meta={
            'provider': 'aws_rekognition',
            'chunk_id': chunk_info['chunk_id'],
            'stage': 'analyzing'
        })
        
        # Initialize provider
        provider = AWSRekognitionProvider()
        
        # Perform analysis
        results = provider.analyze_video_chunk(
            video_path=video_path,
            start_time=chunk_info['start_time'],
            end_time=chunk_info['end_time'],
            chunk_id=chunk_info['chunk_id']
        )
        
        # Cache results
        cache_result(cache_key, results, ttl=86400 * 7)  # Cache for 7 days
        
        return {
            'provider': 'aws_rekognition',
            'chunk_id': chunk_info['chunk_id'],
            'results': results,
            'cached': False
        }
        
    except Exception as e:
        logger.error(f"Rekognition analysis failed for chunk {chunk_info['chunk_id']}: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=120)


@celery_app.task(bind=True, base=VideoProcessingTask, name='workers.video_analysis_tasks.analyze_with_nvidia')
def analyze_with_nvidia(self, video_path: str, chunk_info: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Analyze video chunk with NVIDIA VILA.
    
    Args:
        video_path: S3 path to video chunk
        chunk_info: Chunk metadata
        job_id: Processing job ID
        
    Returns:
        Analysis results from NVIDIA
    """
    try:
        # Check cache first
        cache_key = f"nvidia:{job_id}:{chunk_info['chunk_id']}"
        cached = get_cached_result(cache_key)
        if cached:
            logger.info(f"Using cached NVIDIA results for chunk {chunk_info['chunk_id']}")
            return cached
        
        # Update state
        self.update_state(state='PROGRESS', meta={
            'provider': 'nvidia_vila',
            'chunk_id': chunk_info['chunk_id'],
            'stage': 'analyzing'
        })
        
        # Initialize provider
        provider = NvidiaVilaProvider()
        
        # Perform analysis
        results = provider.analyze_video_chunk(
            video_path=video_path,
            chunk_info=chunk_info
        )
        
        # Cache results
        cache_result(cache_key, results, ttl=86400 * 7)
        
        return {
            'provider': 'nvidia_vila',
            'chunk_id': chunk_info['chunk_id'],
            'results': results,
            'cached': False
        }
        
    except Exception as e:
        logger.error(f"NVIDIA analysis failed for chunk {chunk_info['chunk_id']}: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=180)  # Longer retry for NVIDIA


@celery_app.task(bind=True, name='workers.video_analysis_tasks.merge_provider_results')
@monitor_memory(task_type='video_processing')
def merge_provider_results(self, chunk_id: str, provider_results: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge results from multiple providers for a single chunk.
    
    Args:
        chunk_id: ID of the chunk
        provider_results: List of results from different providers
        
    Returns:
        Merged analysis results
    """
    try:
        merged = {
            'chunk_id': chunk_id,
            'providers': {},
            'merged_data': {
                'objects': [],
                'faces': [],
                'text': [],
                'activities': [],
                'scenes': [],
                'audio_events': [],
                'custom_labels': []
            }
        }
        
        # Merge results from each provider
        for result in provider_results:
            provider = result['provider']
            merged['providers'][provider] = result['results']
            
            # Merge specific data types
            if provider == 'aws_rekognition':
                merged['merged_data']['objects'].extend(result['results'].get('objects', []))
                merged['merged_data']['faces'].extend(result['results'].get('faces', []))
                merged['merged_data']['text'].extend(result['results'].get('text', []))
                merged['merged_data']['custom_labels'].extend(result['results'].get('custom_labels', []))
                
            elif provider == 'nvidia_vila':
                merged['merged_data']['activities'].extend(result['results'].get('activities', []))
                merged['merged_data']['scenes'].extend(result['results'].get('scenes', []))
                merged['merged_data']['audio_events'].extend(result['results'].get('audio_events', []))
        
        # Deduplicate and consolidate
        for key in merged['merged_data']:
            merged['merged_data'][key] = deduplicate_results(merged['merged_data'][key])
        
        return merged
        
    except Exception as e:
        logger.error(f"Failed to merge provider results: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.video_analysis_tasks.extract_keyframes')
@monitor_memory(task_type='video_processing')
def extract_keyframes(self, video_path: str, chunk_info: Dict[str, Any], num_frames: int = 5) -> Dict[str, Any]:
    """
    Extract keyframes from video chunk for visual analysis.
    
    Args:
        video_path: S3 path to video
        chunk_info: Chunk metadata
        num_frames: Number of keyframes to extract
        
    Returns:
        S3 paths to extracted keyframes
    """
    from services.analysis.keyframe_extractor import KeyframeExtractor
    
    try:
        extractor = KeyframeExtractor()
        keyframes = extractor.extract_keyframes(
            video_path=video_path,
            start_time=chunk_info['start_time'],
            end_time=chunk_info['end_time'],
            num_frames=num_frames
        )
        
        return {
            'chunk_id': chunk_info['chunk_id'],
            'keyframes': keyframes,
            'count': len(keyframes)
        }
        
    except Exception as e:
        logger.error(f"Keyframe extraction failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.video_analysis_tasks.detect_shot_boundaries')
def detect_shot_boundaries(self, video_path: str, job_id: str) -> Dict[str, Any]:
    """
    Detect shot boundaries in video for intelligent chunking.
    
    Args:
        video_path: S3 path to video
        job_id: Processing job ID
        
    Returns:
        Shot boundary information
    """
    from services.analysis.shot_detection import ShotDetector
    
    try:
        detector = ShotDetector()
        boundaries = detector.detect_boundaries(video_path)
        
        return {
            'job_id': job_id,
            'boundaries': boundaries,
            'total_shots': len(boundaries)
        }
        
    except Exception as e:
        logger.error(f"Shot detection failed: {str(e)}", exc_info=True)
        raise


def deduplicate_results(results: list) -> list:
    """
    Deduplicate analysis results based on content similarity.
    
    Args:
        results: List of analysis results
        
    Returns:
        Deduplicated results
    """
    from services.utils.deduplication import deduplicate_by_similarity
    
    return deduplicate_by_similarity(results)