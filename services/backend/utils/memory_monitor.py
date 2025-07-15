"""
Memory monitoring utilities for Video Intelligence Platform.
Helps track memory usage and identify memory leaks or high-usage operations,
particularly important for video processing and analysis tasks.
"""

import os
import psutil
import logging
from functools import wraps
from typing import Dict, Optional, Callable, Any
from celery import Task
from celery.signals import task_prerun, task_postrun, worker_process_init

from .logging_config import logger

# Track memory usage for each task
task_memory_usage: Dict[str, Dict[str, Any]] = {}

# Default memory thresholds for Video Intelligence tasks
MEMORY_THRESHOLDS = {
    'default': 3000,  # 3GB default
    'video_processing': 4000,  # 4GB for video tasks
    'embedding_generation': 2000,  # 2GB for embeddings
    'knowledge_graph': 3500,  # 3.5GB for graph operations
}


def get_memory_info() -> Dict[str, float]:
    """Get current memory usage information."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        'percent': process.memory_percent(),
        'available_mb': psutil.virtual_memory().available / 1024 / 1024
    }


def log_memory_usage(context: str = "", extra_data: Optional[Dict] = None) -> Dict[str, float]:
    """
    Log current memory usage with optional context and extra data.
    
    Args:
        context: Description of when/where memory is being logged
        extra_data: Additional data to include in the log
        
    Returns:
        Current memory information
    """
    mem_info = get_memory_info()
    
    log_data = {
        'memory_rss_mb': round(mem_info['rss_mb'], 2),
        'memory_vms_mb': round(mem_info['vms_mb'], 2),
        'memory_percent': round(mem_info['percent'], 2),
        'memory_available_mb': round(mem_info['available_mb'], 2),
        'pid': os.getpid(),
        'context': context
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    logger.info("memory_usage", **log_data)
    return mem_info


@worker_process_init.connect
def init_worker_monitoring(sender=None, **kwargs):
    """Initialize memory monitoring when worker starts."""
    logger.info("worker_initialized", component="memory_monitor")
    log_memory_usage("worker_startup")


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Monitor memory before task execution."""
    mem_info = log_memory_usage(
        f"task_start",
        extra_data={'task_name': task.name, 'task_id': task_id}
    )
    
    task_memory_usage[task_id] = {
        'task_name': task.name,
        'start_memory': mem_info['rss_mb'],
        'args_size': len(str(args)) if args else 0,
        'kwargs_size': len(str(kwargs)) if kwargs else 0
    }


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
    """Monitor memory after task execution and log usage."""
    mem_info = log_memory_usage(
        f"task_complete",
        extra_data={'task_name': task.name, 'task_id': task_id, 'state': state}
    )
    
    if task_id in task_memory_usage:
        start_memory = task_memory_usage[task_id]['start_memory']
        memory_delta = mem_info['rss_mb'] - start_memory
        
        logger.info(
            "task_memory_delta",
            task_name=task.name,
            task_id=task_id,
            memory_delta_mb=round(memory_delta, 2),
            start_memory_mb=round(start_memory, 2),
            final_memory_mb=round(mem_info['rss_mb'], 2),
            state=state
        )
        
        # Warn if task used more than 500MB
        if memory_delta > 500:
            logger.warning(
                "high_memory_usage",
                task_name=task.name,
                task_id=task_id,
                memory_delta_mb=round(memory_delta, 2),
                threshold_mb=500
            )
        
        # Clean up tracking
        del task_memory_usage[task_id]


def monitor_memory(threshold_mb: Optional[float] = None, task_type: str = 'default'):
    """
    Decorator to monitor memory usage for specific functions.
    Logs a warning if memory usage exceeds threshold.
    
    Args:
        threshold_mb: Memory threshold in MB (uses task_type default if not specified)
        task_type: Type of task to determine default threshold
    """
    if threshold_mb is None:
        threshold_mb = MEMORY_THRESHOLDS.get(task_type, MEMORY_THRESHOLDS['default'])
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log memory before
            start_mem = log_memory_usage(
                "function_start",
                extra_data={'function': func.__name__, 'task_type': task_type}
            )
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log memory after
                end_mem = log_memory_usage(
                    "function_complete",
                    extra_data={'function': func.__name__, 'task_type': task_type}
                )
                
                memory_delta = end_mem['rss_mb'] - start_mem['rss_mb']
                
                # Log memory delta
                logger.info(
                    "function_memory_delta",
                    function=func.__name__,
                    memory_delta_mb=round(memory_delta, 2),
                    final_memory_mb=round(end_mem['rss_mb'], 2)
                )
                
                # Check if we exceeded threshold
                if end_mem['rss_mb'] > threshold_mb:
                    logger.warning(
                        "memory_threshold_exceeded",
                        function=func.__name__,
                        memory_mb=round(end_mem['rss_mb'], 2),
                        threshold_mb=threshold_mb,
                        task_type=task_type
                    )
                
                return result
                
            except Exception as e:
                # Log memory on error too
                error_mem = log_memory_usage(
                    "function_error",
                    extra_data={'function': func.__name__, 'error': str(e)}
                )
                logger.error(
                    "function_failed_with_memory_state",
                    function=func.__name__,
                    memory_mb=round(error_mem['rss_mb'], 2),
                    error=str(e),
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


class MemoryAwareTask(Task):
    """
    Base task class that includes memory monitoring.
    Suitable for Video Intelligence heavy processing tasks.
    """
    
    # Override these in subclasses
    memory_threshold_mb = 3500  # Default 3.5GB
    task_type = 'default'
    
    def __call__(self, *args, **kwargs):
        """Override to add memory monitoring."""
        # Log memory at task start
        mem_info = log_memory_usage(
            "memory_aware_task_start",
            extra_data={
                'task_name': self.name,
                'task_type': self.task_type
            }
        )
        
        # Check if we're already using too much memory
        if mem_info['rss_mb'] > self.memory_threshold_mb:
            logger.error(
                "task_starting_with_high_memory",
                task_name=self.name,
                memory_mb=round(mem_info['rss_mb'], 2),
                threshold_mb=self.memory_threshold_mb,
                task_type=self.task_type
            )
            
            # Optionally, we could refuse to run if memory is too high
            # raise MemoryError(f"Insufficient memory to start task {self.name}")
        
        return super().__call__(*args, **kwargs)


class VideoProcessingTask(MemoryAwareTask):
    """Specialized task for video processing with higher memory threshold."""
    memory_threshold_mb = 4000  # 4GB for video tasks
    task_type = 'video_processing'


class EmbeddingTask(MemoryAwareTask):
    """Specialized task for embedding generation with lower memory threshold."""
    memory_threshold_mb = 2000  # 2GB for embedding tasks
    task_type = 'embedding_generation'


class KnowledgeGraphTask(MemoryAwareTask):
    """Specialized task for knowledge graph operations."""
    memory_threshold_mb = 3500  # 3.5GB for graph tasks
    task_type = 'knowledge_graph'


def check_memory_health(warn_threshold_percent: float = 80.0) -> Dict[str, Any]:
    """
    Check overall system memory health and return status.
    
    Args:
        warn_threshold_percent: Percentage of memory usage to trigger warning
        
    Returns:
        Dictionary with memory health status
    """
    mem_info = get_memory_info()
    system_memory = psutil.virtual_memory()
    
    health_status = {
        'healthy': system_memory.percent < warn_threshold_percent,
        'process_rss_mb': round(mem_info['rss_mb'], 2),
        'system_percent_used': round(system_memory.percent, 2),
        'system_available_gb': round(system_memory.available / 1024 / 1024 / 1024, 2),
        'warning_threshold_percent': warn_threshold_percent
    }
    
    if not health_status['healthy']:
        logger.warning("memory_health_warning", **health_status)
    
    return health_status