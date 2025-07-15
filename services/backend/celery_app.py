from celery import Celery
import os

# Import memory monitoring to register signal handlers
import utils.memory_monitor

# Environment variables for configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery for Video Intelligence Platform
celery_app = Celery(
    "video_intelligence",  # Updated app name for new project
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        # Video Intelligence specific task modules
        "workers.ingestion_tasks",      # Phase 1: Heavy preprocessing tasks
        "workers.video_analysis_tasks",  # Video analysis with providers
        "workers.embedding_tasks",       # Embedding generation
        "workers.knowledge_graph_tasks", # Knowledge graph construction
        "workers.rag_tasks",            # RAG and retrieval tasks
        "workers.orchestration_tasks",   # Task orchestration and coordination
    ]
)

# Configuration optimized for Video Intelligence workloads
celery_app.conf.update(
    # Serialization settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Time limits for long-running video processing
    task_time_limit=7200,  # 2 hours hard limit for video tasks
    task_soft_time_limit=6000,  # 100 minutes soft limit
    
    # Result backend settings
    result_expires=86400 * 30,  # Keep results for 30 days (ingestion phase results)
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 7200,  # 2 hours
        'fanout_prefix': True,
        'fanout_patterns': True
    },
    
    # Worker optimization for video processing
    worker_prefetch_multiplier=1,  # One task at a time for heavy video processing
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,  # Reject if worker dies
    
    # Task tracking and monitoring
    task_track_started=True,
    task_send_sent_event=True,  # Track all task events
    worker_send_task_events=True,  # Send task events for monitoring
    
    # Memory management - critical for video processing
    worker_max_tasks_per_child=25,  # Restart after 25 tasks (heavy video processing)
    worker_max_memory_per_child=4096000,  # Restart if using more than 4GB RAM
    
    # Queue routing for two-phase architecture
    task_routes={
        # Ingestion phase tasks (heavy processing)
        'workers.ingestion_tasks.*': {'queue': 'ingestion'},
        'workers.video_analysis_tasks.*': {'queue': 'video_analysis'},
        'workers.embedding_tasks.*': {'queue': 'embeddings'},
        'workers.knowledge_graph_tasks.*': {'queue': 'knowledge_graph'},
        
        # Runtime phase tasks (lightweight)
        'workers.rag_tasks.*': {'queue': 'runtime'},
        
        # Orchestration
        'workers.orchestration_tasks.*': {'queue': 'orchestration'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'exchange_type': 'direct',
            'routing_key': 'default',
        },
        'ingestion': {
            'exchange': 'ingestion',
            'exchange_type': 'direct',
            'routing_key': 'ingestion',
            'priority': 5,  # Lower priority for heavy tasks
        },
        'video_analysis': {
            'exchange': 'video_analysis',
            'exchange_type': 'direct',
            'routing_key': 'video_analysis',
            'priority': 5,
        },
        'embeddings': {
            'exchange': 'embeddings',
            'exchange_type': 'direct',
            'routing_key': 'embeddings',
            'priority': 7,
        },
        'knowledge_graph': {
            'exchange': 'knowledge_graph',
            'exchange_type': 'direct',
            'routing_key': 'knowledge_graph',
            'priority': 6,
        },
        'runtime': {
            'exchange': 'runtime',
            'exchange_type': 'direct',
            'routing_key': 'runtime',
            'priority': 10,  # High priority for runtime queries
        },
        'orchestration': {
            'exchange': 'orchestration',
            'exchange_type': 'direct',
            'routing_key': 'orchestration',
            'priority': 8,
        },
    },
    
    # Beat schedule for periodic tasks (if needed)
    beat_schedule={
        # Example: Clean up old processing jobs
        'cleanup-old-jobs': {
            'task': 'workers.orchestration_tasks.cleanup_old_jobs',
            'schedule': 86400.0,  # Daily
            'options': {'queue': 'orchestration'}
        },
    },
    
    # Canvas operations for complex workflows
    task_always_eager=False,  # Never run tasks synchronously
    task_eager_propagates=True,
    
    # Error handling
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Monitoring and events
    worker_hijack_root_logger=False,  # Don't hijack root logger
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Additional settings for production
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    
    # Result backend settings
    result_backend_always_retry=True,
    result_backend_max_retries=10,
    
    # Security
    worker_disable_rate_limits=False,
    task_compression='gzip',  # Compress task payloads
)

# Configure Celery to work with MongoDB models
celery_app.conf.update(
    # Custom task base name format
    task_name_format='video_intelligence.{module}.{function}',
    
    # MongoDB integration settings
    mongodb_backend_settings={
        'database': os.getenv('MONGODB_DATABASE', 'video_intelligence'),
        'taskmeta_collection': 'celery_taskmeta',
    }
)

if __name__ == "__main__":
    # For running the worker directly
    # celery -A celery_app worker -l info -Q default,ingestion,video_analysis,embeddings,knowledge_graph,runtime,orchestration
    celery_app.start()