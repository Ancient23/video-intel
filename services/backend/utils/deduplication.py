"""
Request deduplication utility for preventing duplicate processing.

This module prevents multiple identical requests from triggering duplicate processing
by using Redis to track active tasks and return existing task IDs for identical requests.

Implemented for the Video Intelligence Platform.
"""

import redis
import json
import hashlib
import os
import structlog
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)

class DeduplicationClient:
    """Redis-based request deduplication client."""
    
    def __init__(self):
        """Initialize Redis connection with fallback to local connection."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis deduplication service", redis_url=redis_url)
        except Exception as e:
            logger.warning("Failed to connect to Redis deduplication service", error=str(e))
            self.redis_client = None
    
    def _generate_request_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate deterministic key for deduplication."""
        # Sort parameters for consistent hashing
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:16]
        return f"dedup:{operation}:{params_hash}"
    
    def _generate_task_key(self, task_id: str) -> str:
        """Generate key for tracking active tasks."""
        return f"active_task:{task_id}"
    
    def check_existing_task(self, operation: str, params: Dict[str, Any]) -> Optional[str]:
        """
        Check if an identical request is already being processed.
        
        Args:
            operation: Operation type (e.g., 'video_ingestion', 'knowledge_extraction', 
                      'embedding_generation', 'graph_construction', 'rag_indexing')
            params: Request parameters
            
        Returns:
            Existing task ID if found, None otherwise
        """
        if not self.redis_client:
            return None
            
        try:
            request_key = self._generate_request_key(operation, params)
            existing_task_id = self.redis_client.get(request_key)
            
            if existing_task_id:
                # Verify the task is still active
                task_key = self._generate_task_key(existing_task_id)
                task_data = self.redis_client.get(task_key)
                
                if task_data:
                    task_info = json.loads(task_data)
                    logger.info("Found existing task for duplicate request", 
                               operation=operation, 
                               request_key=request_key,
                               existing_task_id=existing_task_id,
                               task_started_at=task_info.get('started_at'))
                    return existing_task_id
                else:
                    # Task data expired, clean up the request key
                    self.redis_client.delete(request_key)
                    logger.debug("Cleaned up expired request mapping", request_key=request_key)
            
            return None
            
        except Exception as e:
            logger.warning("Deduplication check failed", operation=operation, error=str(e))
            return None
    
    def register_task(self, operation: str, params: Dict[str, Any], task_id: str, 
                     ttl_hours: int = 24) -> bool:
        """
        Register a new task for deduplication tracking.
        
        Args:
            operation: Operation type
            params: Request parameters
            task_id: Celery task ID
            ttl_hours: How long to track this task (default 24 hours)
            
        Returns:
            True if registered successfully, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            request_key = self._generate_request_key(operation, params)
            task_key = self._generate_task_key(task_id)
            ttl_seconds = ttl_hours * 60 * 60
            
            # Store task information
            task_data = {
                'task_id': task_id,
                'operation': operation,
                'started_at': datetime.utcnow().isoformat(),
                'params_hash': hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16],
                'ttl_hours': ttl_hours
            }
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.setex(request_key, ttl_seconds, task_id)
            pipe.setex(task_key, ttl_seconds, json.dumps(task_data))
            pipe.execute()
            
            logger.info("Registered task for deduplication", 
                       operation=operation, 
                       task_id=task_id,
                       request_key=request_key,
                       ttl_hours=ttl_hours)
            return True
            
        except Exception as e:
            logger.warning("Task registration failed", operation=operation, task_id=task_id, error=str(e))
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """
        Mark a task as completed and clean up deduplication tracking.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            True if cleaned up successfully, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            task_key = self._generate_task_key(task_id)
            task_data = self.redis_client.get(task_key)
            
            if task_data:
                task_info = json.loads(task_data)
                operation = task_info.get('operation')
                params_hash = task_info.get('params_hash')
                
                # Clean up both task and request keys
                request_key = f"dedup:{operation}:{params_hash}"
                
                pipe = self.redis_client.pipeline()
                pipe.delete(task_key)
                pipe.delete(request_key)
                deleted_count = pipe.execute()
                
                logger.info("Cleaned up completed task deduplication", 
                           task_id=task_id,
                           operation=operation,
                           deleted_keys=sum(deleted_count))
                return True
            else:
                logger.debug("Task not found in deduplication tracking", task_id=task_id)
                return False
                
        except Exception as e:
            logger.warning("Task cleanup failed", task_id=task_id, error=str(e))
            return False
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics for monitoring."""
        if not self.redis_client:
            return {"error": "Redis not available"}
            
        try:
            # Count active tasks and request mappings
            active_tasks = self.redis_client.keys("active_task:*")
            request_mappings = self.redis_client.keys("dedup:*")
            
            # Get operation breakdown
            operations = {}
            for key in request_mappings:
                try:
                    parts = key.split(':')
                    if len(parts) >= 2:
                        operation = parts[1]
                        operations[operation] = operations.get(operation, 0) + 1
                except:
                    continue
            
            return {
                'active_tasks': len(active_tasks),
                'request_mappings': len(request_mappings),
                'operations': operations,
                'deduplication_ratio': len(request_mappings) / max(len(active_tasks), 1) if active_tasks else 0
            }
            
        except Exception as e:
            logger.warning("Deduplication stats error", error=str(e))
            return {"error": str(e)}


# Global deduplication client instance
dedup_client = DeduplicationClient()


def deduplicate_request(operation: str, ttl_hours: int = 24):
    """
    Decorator for request deduplication.
    
    Usage:
        @deduplicate_request('video_ingestion', ttl_hours=12)
        def process_video_ingestion(params):
            # Expensive processing here
            return task_id
            
    Video Intelligence Platform specific operations:
        - video_ingestion: Initial video processing and chunking
        - knowledge_extraction: Extract entities, events, relationships
        - embedding_generation: Generate embeddings for chunks
        - graph_construction: Build knowledge graph
        - rag_indexing: Index for retrieval
        - multi_modal_analysis: Combined visual/audio/text analysis
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract parameters for deduplication key
            # For task submission functions, typically the first arg or kwargs contain request params
            params = {}
            if args:
                if hasattr(args[0], '__dict__'):
                    # Pydantic model or similar
                    params = args[0].model_dump() if hasattr(args[0], 'model_dump') else args[0].__dict__
                elif isinstance(args[0], dict):
                    params = args[0]
                else:
                    # Convert to string for primitive types
                    params = {'primary_param': str(args[0])}
            
            # Check for existing task
            existing_task_id = dedup_client.check_existing_task(operation, params)
            if existing_task_id:
                logger.info("Request deduplicated", operation=operation, existing_task_id=existing_task_id)
                return {'task_id': existing_task_id, 'deduplicated': True}
            
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Register the new task if result contains task_id
            if isinstance(result, dict) and 'task_id' in result:
                dedup_client.register_task(operation, params, result['task_id'], ttl_hours)
            elif hasattr(result, 'id'):  # Celery AsyncResult
                dedup_client.register_task(operation, params, result.id, ttl_hours)
            
            return result
        
        return wrapper
    return decorator


def cleanup_completed_task(task_id: str):
    """
    Clean up deduplication tracking for a completed task.
    Should be called when a task completes (success or failure).
    """
    return dedup_client.complete_task(task_id)


# Video Intelligence specific operation types
VIDEO_INTELLIGENCE_OPERATIONS = [
    'video_ingestion',
    'knowledge_extraction',
    'embedding_generation', 
    'graph_construction',
    'rag_indexing',
    'multi_modal_analysis',
    'scene_detection',
    'entity_extraction',
    'relationship_mapping',
    'temporal_analysis'
]