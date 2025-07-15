"""Utility modules for the Video Intelligence Platform."""

from .cache import cache_client, cache_api_call, get_video_hash
from .logging_config import logger, get_logger, configure_logging
from .memory_monitor import (
    get_memory_info,
    log_memory_usage,
    monitor_memory,
    check_memory_health,
    MemoryAwareTask,
    VideoProcessingTask,
    EmbeddingTask,
    KnowledgeGraphTask,
)
from .deduplication import (
    dedup_client,
    deduplicate_request,
    cleanup_completed_task,
    DeduplicationClient,
    VIDEO_INTELLIGENCE_OPERATIONS,
)

__all__ = [
    # Cache utilities
    'cache_client',
    'cache_api_call',
    'get_video_hash',
    # Logging utilities
    'logger',
    'get_logger',
    'configure_logging',
    # Memory monitoring utilities
    'get_memory_info',
    'log_memory_usage',
    'monitor_memory',
    'check_memory_health',
    'MemoryAwareTask',
    'VideoProcessingTask',
    'EmbeddingTask',
    'KnowledgeGraphTask',
    # Deduplication utilities
    'dedup_client',
    'deduplicate_request',
    'cleanup_completed_task',
    'DeduplicationClient',
    'VIDEO_INTELLIGENCE_OPERATIONS',
]