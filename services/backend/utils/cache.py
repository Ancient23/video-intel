"""
Redis caching utility for expensive API calls in Video Intelligence Platform.

This module provides caching for:
- AWS Rekognition detection results (save 30-40%)  
- AWS Transcribe results (save 40%)
- OpenAI GPT script generation (save 60% with smart model selection)
- ElevenLabs TTS audio generation (save 40%)
- NVIDIA VILA analysis results
- Knowledge graph construction results
- Embedding generation results

Cache keys are generated using content hashes to ensure cache hits
for identical requests across different users/sessions.
"""

import redis
import json
import hashlib
import os
import structlog
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)

class CacheClient:
    """Redis cache client for expensive API call results."""
    
    def __init__(self):
        """Initialize Redis connection with fallback to local connection."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis cache", redis_url=redis_url)
        except Exception as e:
            logger.warning("Failed to connect to Redis cache", error=str(e))
            self.redis_client = None
    
    def _generate_cache_key(self, service: str, content_hash: str, params_hash: str) -> str:
        """Generate consistent cache key for API calls."""
        return f"api_cache:{service}:{content_hash}:{params_hash}"
    
    def _hash_content(self, content: Union[str, bytes, Dict[str, Any]]) -> str:
        """Generate SHA256 hash of content for cache key."""
        if isinstance(content, dict):
            # Sort keys for consistent hashing
            content_str = json.dumps(content, sort_keys=True)
        elif isinstance(content, bytes):
            content_str = content.hex()
        else:
            content_str = str(content)
        
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Generate hash of API parameters for cache key."""
        return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    
    def get(self, service: str, content: Union[str, bytes, Dict[str, Any]], 
            params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached API result.
        
        Args:
            service: API service name (rekognition, transcribe, openai, elevenlabs, nvidia_vila, knowledge_graph, embeddings)
            content: Content being processed (video bytes, text, etc.)
            params: API call parameters
            
        Returns:
            Cached result dict or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            content_hash = self._hash_content(content)
            params_hash = self._hash_params(params or {})
            cache_key = self._generate_cache_key(service, content_hash, params_hash)
            
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                logger.info("Cache hit", service=service, cache_key=cache_key, 
                           cached_at=result.get('cached_at'))
                return result.get('data')
            
            logger.debug("Cache miss", service=service, cache_key=cache_key)
            return None
            
        except Exception as e:
            logger.warning("Cache get error", service=service, error=str(e))
            return None
    
    def set(self, service: str, content: Union[str, bytes, Dict[str, Any]], 
            result: Dict[str, Any], params: Dict[str, Any] = None, 
            ttl_days: int = None) -> bool:
        """
        Cache API result with appropriate TTL.
        
        Args:
            service: API service name
            content: Content that was processed
            result: API result to cache
            params: API call parameters
            ttl_days: Cache TTL in days (uses service defaults if None)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            # Default TTL by service (based on cost optimization analysis)
            default_ttls = {
                'rekognition': 7,          # Video analysis changes rarely
                'transcribe': 30,          # Transcripts never change for same video
                'openai': 14,              # Scripts may be regenerated with different styles  
                'elevenlabs': 90,          # Audio never changes for same script
                'shot_detection': 30,      # Shot boundaries never change
                'nvidia_vila': 7,          # NVIDIA analysis results
                'knowledge_graph': 14,     # Knowledge graph construction
                'embeddings': 30,          # Embeddings for same content
                'scene_analysis': 7,       # Scene analysis results
                'chunk_processing': 7,     # Chunk processing results
            }
            
            ttl_days = ttl_days or default_ttls.get(service, 7)
            ttl_seconds = ttl_days * 24 * 60 * 60
            
            content_hash = self._hash_content(content)
            params_hash = self._hash_params(params or {})
            cache_key = self._generate_cache_key(service, content_hash, params_hash)
            
            cache_data = {
                'data': result,
                'service': service,
                'cached_at': datetime.utcnow().isoformat(),
                'ttl_days': ttl_days,
                'content_hash': content_hash,
                'params_hash': params_hash
            }
            
            self.redis_client.setex(cache_key, ttl_seconds, json.dumps(cache_data))
            
            logger.info("Cached API result", service=service, cache_key=cache_key, 
                       ttl_days=ttl_days, data_size_bytes=len(json.dumps(result)))
            return True
            
        except Exception as e:
            logger.warning("Cache set error", service=service, error=str(e))
            return False
    
    def invalidate(self, service: str, content: Union[str, bytes, Dict[str, Any]], 
                   params: Dict[str, Any] = None) -> bool:
        """
        Invalidate cached result.
        
        Args:
            service: API service name
            content: Content that was processed
            params: API call parameters
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            content_hash = self._hash_content(content)
            params_hash = self._hash_params(params or {})
            cache_key = self._generate_cache_key(service, content_hash, params_hash)
            
            deleted = self.redis_client.delete(cache_key)
            logger.info("Cache invalidated", service=service, cache_key=cache_key, 
                       was_cached=bool(deleted))
            return bool(deleted)
            
        except Exception as e:
            logger.warning("Cache invalidate error", service=service, error=str(e))
            return False
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "api_cache:rekognition:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info("Bulk cache invalidation", pattern=pattern, deleted_count=deleted)
                return deleted
            return 0
            
        except Exception as e:
            logger.warning("Bulk cache invalidate error", pattern=pattern, error=str(e))
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        if not self.redis_client:
            return {"error": "Redis not available"}
            
        try:
            info = self.redis_client.info()
            
            # Get cache keys by service
            services = [
                'rekognition', 'transcribe', 'openai', 'elevenlabs', 
                'shot_detection', 'nvidia_vila', 'knowledge_graph', 
                'embeddings', 'scene_analysis', 'chunk_processing'
            ]
            service_stats = {}
            
            for service in services:
                pattern = f"api_cache:{service}:*"
                keys = self.redis_client.keys(pattern)
                service_stats[service] = {
                    'cached_items': len(keys),
                    'estimated_size_mb': sum(len(self.redis_client.get(key) or '') for key in keys[:100]) / 1024 / 1024
                }
            
            return {
                'redis_info': {
                    'used_memory_mb': info.get('used_memory', 0) / 1024 / 1024,
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                },
                'service_stats': service_stats,
                'total_api_cache_keys': sum(stats['cached_items'] for stats in service_stats.values())
            }
            
        except Exception as e:
            logger.warning("Cache stats error", error=str(e))
            return {"error": str(e)}


# Global cache client instance
cache_client = CacheClient()


def cache_api_call(service: str, ttl_days: int = None):
    """
    Decorator for caching expensive API calls.
    
    Usage:
        @cache_api_call('rekognition', ttl_days=7)
        def analyze_video_with_rekognition(video_bytes, params):
            # Expensive API call here
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract content and params for cache key
            content = args[0] if args else None
            params = kwargs.copy()
            
            # Check cache first
            cached_result = cache_client.get(service, content, params)
            if cached_result is not None:
                return cached_result
            
            # Make API call
            result = func(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                cache_client.set(service, content, result, params, ttl_days)
            
            return result
        
        return wrapper
    return decorator


def get_video_hash(video_s3_key: str, s3_client) -> str:
    """
    Generate hash of video content for caching.
    Uses S3 ETag if available, otherwise downloads first 1MB for hashing.
    """
    try:
        # Get S3 object metadata
        bucket = os.getenv('S3_BUCKET', os.getenv('S3_INPUT_BUCKET'))
        response = s3_client.head_object(Bucket=bucket, Key=video_s3_key)
        etag = response.get('ETag', '').strip('"')
        
        if etag and '-' not in etag:  # Simple ETag (not multipart upload)
            return etag
        
        # For multipart uploads or missing ETag, hash first 1MB
        response = s3_client.get_object(
            Bucket=bucket, 
            Key=video_s3_key,
            Range='bytes=0-1048576'  # First 1MB
        )
        
        content_sample = response['Body'].read()
        return hashlib.sha256(content_sample).hexdigest()[:16]
        
    except Exception as e:
        logger.warning("Failed to generate video hash", s3_key=video_s3_key, error=str(e))
        # Fallback to S3 key hash
        return hashlib.sha256(video_s3_key.encode()).hexdigest()[:16]


def cache_chunk_result(chunk_id: str, provider: str, result: Dict[str, Any], ttl_days: int = 7) -> bool:
    """
    Cache analysis result for a specific video chunk.
    
    Args:
        chunk_id: Unique identifier for the chunk
        provider: Analysis provider (rekognition, nvidia_vila)
        result: Analysis result to cache
        ttl_days: Cache TTL in days
        
    Returns:
        True if cached successfully
    """
    cache_key = f"chunk:{chunk_id}:provider:{provider}"
    return cache_client.set('chunk_processing', cache_key, result, ttl_days=ttl_days)


def get_cached_chunk_result(chunk_id: str, provider: str) -> Optional[Dict[str, Any]]:
    """
    Get cached analysis result for a specific video chunk.
    
    Args:
        chunk_id: Unique identifier for the chunk
        provider: Analysis provider (rekognition, nvidia_vila)
        
    Returns:
        Cached result or None
    """
    cache_key = f"chunk:{chunk_id}:provider:{provider}"
    return cache_client.get('chunk_processing', cache_key)


def invalidate_video_cache(video_id: str) -> int:
    """
    Invalidate all cache entries related to a specific video.
    
    Args:
        video_id: Video identifier
        
    Returns:
        Number of cache entries invalidated
    """
    patterns = [
        f"api_cache:*:*{video_id}*",
        f"chunk:*{video_id}*:provider:*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        total_deleted += cache_client.invalidate_by_pattern(pattern)
    
    return total_deleted