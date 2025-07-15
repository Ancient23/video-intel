"""
Embedding generation tasks for Video Intelligence Platform.

These tasks handle embedding generation for various data types
extracted during video analysis.
"""

from celery import group, chord
from celery_app import celery_app
from utils.memory_monitor import EmbeddingTask, monitor_memory
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=EmbeddingTask, name='workers.embedding_tasks.generate_text_embeddings')
def generate_text_embeddings(self, texts: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Generate embeddings for text content (transcripts, OCR, descriptions).
    
    Args:
        texts: List of text items with metadata
        job_id: Processing job ID
        
    Returns:
        Embedding results
    """
    from services.embeddings.text_embedder import TextEmbedder
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'generating_text_embeddings',
            'total_texts': len(texts)
        })
        
        embedder = TextEmbedder()
        embeddings = []
        
        # Process in batches for efficiency
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = embedder.embed_batch(batch, job_id)
            embeddings.extend(batch_embeddings)
            
            # Update progress
            progress = min(90, int((i + batch_size) / len(texts) * 90))
            self.update_state(state='PROGRESS', meta={
                'stage': 'generating_text_embeddings',
                'progress': progress,
                'processed': i + len(batch)
            })
        
        return {
            'job_id': job_id,
            'embedding_type': 'text',
            'total_embeddings': len(embeddings),
            'embedding_ids': [e['id'] for e in embeddings],
            'vector_dimension': embedder.dimension
        }
        
    except Exception as e:
        logger.error(f"Text embedding generation failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, base=EmbeddingTask, name='workers.embedding_tasks.generate_visual_embeddings')
def generate_visual_embeddings(self, images: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Generate embeddings for visual content (keyframes, detected objects).
    
    Args:
        images: List of image paths with metadata
        job_id: Processing job ID
        
    Returns:
        Embedding results
    """
    from services.embeddings.visual_embedder import VisualEmbedder
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'generating_visual_embeddings',
            'total_images': len(images)
        })
        
        embedder = VisualEmbedder()
        embeddings = []
        
        # Process images
        for idx, image_data in enumerate(images):
            embedding = embedder.embed_image(
                image_path=image_data['path'],
                metadata=image_data.get('metadata', {}),
                job_id=job_id
            )
            embeddings.append(embedding)
            
            # Update progress
            if idx % 10 == 0:
                self.update_state(state='PROGRESS', meta={
                    'stage': 'generating_visual_embeddings',
                    'progress': int((idx + 1) / len(images) * 100),
                    'processed': idx + 1
                })
        
        return {
            'job_id': job_id,
            'embedding_type': 'visual',
            'total_embeddings': len(embeddings),
            'embedding_ids': [e['id'] for e in embeddings],
            'vector_dimension': embedder.dimension
        }
        
    except Exception as e:
        logger.error(f"Visual embedding generation failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=90)


@celery_app.task(bind=True, base=EmbeddingTask, name='workers.embedding_tasks.generate_multimodal_embeddings')
def generate_multimodal_embeddings(self, content: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Generate unified multimodal embeddings combining text and visual features.
    
    Args:
        content: Dictionary with text and visual content
        job_id: Processing job ID
        
    Returns:
        Multimodal embedding results
    """
    from services.embeddings.multimodal_embedder import MultimodalEmbedder
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'generating_multimodal_embeddings'
        })
        
        embedder = MultimodalEmbedder()
        embeddings = embedder.embed_multimodal(
            text_content=content.get('text', []),
            visual_content=content.get('visual', []),
            audio_features=content.get('audio', []),
            job_id=job_id
        )
        
        return {
            'job_id': job_id,
            'embedding_type': 'multimodal',
            'total_embeddings': len(embeddings),
            'embedding_ids': [e['id'] for e in embeddings],
            'vector_dimension': embedder.dimension
        }
        
    except Exception as e:
        logger.error(f"Multimodal embedding generation failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=120)


@celery_app.task(bind=True, name='workers.embedding_tasks.index_embeddings')
@monitor_memory(task_type='embedding_generation')
def index_embeddings(self, embedding_results: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Index embeddings in vector database for efficient retrieval.
    
    Args:
        embedding_results: Results from embedding generation
        job_id: Processing job ID
        
    Returns:
        Indexing results
    """
    from services.embeddings.vector_indexer import VectorIndexer
    
    try:
        indexer = VectorIndexer()
        
        # Collect all embeddings
        all_embeddings = []
        for result in embedding_results:
            all_embeddings.extend(result.get('embeddings', []))
        
        # Index in vector database
        index_results = indexer.index_embeddings(
            embeddings=all_embeddings,
            job_id=job_id,
            create_index=True
        )
        
        return {
            'job_id': job_id,
            'total_indexed': index_results['indexed_count'],
            'index_name': index_results['index_name'],
            'vector_db': index_results['vector_db_type']
        }
        
    except Exception as e:
        logger.error(f"Embedding indexing failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.embedding_tasks.generate_chunk_embeddings')
def generate_chunk_embeddings(self, chunk_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Generate all embeddings for a single video chunk.
    
    Args:
        chunk_data: Chunk analysis data
        job_id: Processing job ID
        
    Returns:
        All embeddings for the chunk
    """
    try:
        # Prepare content for embedding
        text_content = []
        visual_content = []
        
        # Extract text content
        if 'transcript' in chunk_data:
            text_content.append({
                'text': chunk_data['transcript'],
                'type': 'transcript',
                'chunk_id': chunk_data['chunk_id']
            })
        
        if 'detected_text' in chunk_data:
            for text in chunk_data['detected_text']:
                text_content.append({
                    'text': text['text'],
                    'type': 'ocr',
                    'chunk_id': chunk_data['chunk_id'],
                    'timestamp': text.get('timestamp')
                })
        
        # Extract visual content
        if 'keyframes' in chunk_data:
            for keyframe in chunk_data['keyframes']:
                visual_content.append({
                    'path': keyframe['s3_path'],
                    'type': 'keyframe',
                    'chunk_id': chunk_data['chunk_id'],
                    'timestamp': keyframe['timestamp']
                })
        
        # Create embedding tasks
        tasks = []
        
        if text_content:
            tasks.append(
                generate_text_embeddings.signature(
                    args=[text_content, job_id],
                    queue='embeddings'
                )
            )
        
        if visual_content:
            tasks.append(
                generate_visual_embeddings.signature(
                    args=[visual_content, job_id],
                    queue='embeddings'
                )
            )
        
        # Execute in parallel
        embedding_group = group(tasks)
        results = embedding_group.apply_async().get()
        
        # Generate multimodal embedding
        multimodal_result = generate_multimodal_embeddings.apply_async(
            args=[{
                'text': text_content,
                'visual': visual_content,
                'chunk_id': chunk_data['chunk_id']
            }, job_id],
            queue='embeddings'
        ).get()
        
        results.append(multimodal_result)
        
        return {
            'chunk_id': chunk_data['chunk_id'],
            'embeddings': results,
            'total_embeddings': sum(r['total_embeddings'] for r in results)
        }
        
    except Exception as e:
        logger.error(f"Chunk embedding generation failed: {str(e)}", exc_info=True)
        raise