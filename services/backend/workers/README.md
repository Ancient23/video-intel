# Celery Workers for Video Intelligence Platform

This directory contains all Celery task definitions for the Video Intelligence Platform, organized according to the two-phase architecture.

## Architecture Overview

The platform uses a two-phase system:

1. **Ingestion Phase** (Heavy Processing)
   - Video analysis with multiple AI providers
   - Embedding generation
   - Knowledge graph construction
   - Heavy preprocessing to extract comprehensive knowledge

2. **Runtime Phase** (Lightweight)
   - RAG queries and retrieval
   - Semantic search
   - Real-time conversational AI

## Task Modules

### Ingestion Phase Tasks

- **`ingestion_tasks.py`**: Main ingestion orchestration
  - `process_video`: Main entry point for video processing
  - `chunk_video`: Video segmentation
  - `analyze_chunk`: Chunk analysis coordination

- **`video_analysis_tasks.py`**: Provider-specific analysis
  - `analyze_with_rekognition`: AWS Rekognition analysis
  - `analyze_with_nvidia`: NVIDIA VILA analysis
  - `extract_keyframes`: Keyframe extraction
  - `detect_shot_boundaries`: Shot detection

- **`embedding_tasks.py`**: Embedding generation
  - `generate_text_embeddings`: Text content embeddings
  - `generate_visual_embeddings`: Visual content embeddings
  - `generate_multimodal_embeddings`: Combined embeddings
  - `index_embeddings`: Vector database indexing

- **`knowledge_graph_tasks.py`**: Graph construction
  - `extract_entities`: Entity extraction
  - `extract_relationships`: Relationship extraction
  - `build_scene_graph`: Scene-level graphs
  - `merge_knowledge_graphs`: Graph merging

### Runtime Phase Tasks

- **`rag_tasks.py`**: Retrieval and generation
  - `semantic_search`: Vector similarity search
  - `graph_traversal_search`: Knowledge graph queries
  - `hybrid_search`: Combined search
  - `generate_context`: Context preparation
  - `answer_query`: LLM response generation

### Supporting Tasks

- **`orchestration_tasks.py`**: Workflow management
  - `orchestrate_video_ingestion`: Complete workflow orchestration
  - `batch_process_videos`: Batch processing
  - `retry_failed_tasks`: Error recovery
  - `cleanup_old_jobs`: Maintenance tasks

## Running Workers

### Development

Start all workers:
```bash
celery -A celery_app worker -l info -Q default,ingestion,video_analysis,embeddings,knowledge_graph,runtime,orchestration
```

Start specific queue workers:
```bash
# Ingestion workers (high memory)
celery -A celery_app worker -l info -Q ingestion,video_analysis -n ingestion-worker --max-memory-per-child=4096000

# Embedding workers (GPU preferred)
celery -A celery_app worker -l info -Q embeddings -n embedding-worker --max-memory-per-child=2048000

# Runtime workers (low latency)
celery -A celery_app worker -l info -Q runtime -n runtime-worker --max-memory-per-child=1024000
```

### Production

Use supervisor or systemd to manage workers:

```ini
[program:video-intelligence-ingestion-worker]
command=celery -A celery_app worker -Q ingestion,video_analysis -n ingestion-worker-%%i --max-memory-per-child=4096000
process_name=%(program_name)s_%(process_num)02d
numprocs=2
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/ingestion-worker.log
```

## Queue Configuration

| Queue | Purpose | Priority | Memory Limit | Typical Duration |
|-------|---------|----------|--------------|------------------|
| `default` | General tasks | 5 | 2GB | < 5 min |
| `ingestion` | Main video processing | 5 | 4GB | 10-60 min |
| `video_analysis` | Provider analysis | 5 | 4GB | 5-30 min |
| `embeddings` | Embedding generation | 7 | 2GB | 2-10 min |
| `knowledge_graph` | Graph construction | 6 | 3.5GB | 5-20 min |
| `runtime` | Query processing | 10 | 1GB | < 1 min |
| `orchestration` | Workflow management | 8 | 0.5GB | < 5 min |

## Memory Management

The configuration includes automatic memory management:

- **Worker recycling**: Workers restart after 25 tasks
- **Memory limits**: Workers restart if exceeding memory threshold
- **Memory monitoring**: All tasks track memory usage
- **Task-specific limits**: Different task types have different thresholds

## Error Handling

- **Automatic retries**: 3 retries with exponential backoff
- **Dead letter queue**: Failed tasks after max retries
- **Task acknowledgment**: Only after successful completion
- **Graceful shutdown**: Soft time limits before hard limits

## Monitoring

Monitor workers with Flower:
```bash
celery -A celery_app flower --port=5555
```

Key metrics to monitor:
- Task completion rates
- Memory usage per worker
- Queue lengths
- Task duration percentiles
- Failed task reasons

## Best Practices

1. **Use task signatures** for dynamic workflows
2. **Cache analysis results** to avoid reprocessing
3. **Monitor memory usage** especially for video tasks
4. **Use Canvas patterns** (group, chain, chord) for complex workflows
5. **Set appropriate timeouts** based on video duration
6. **Log task progress** for long-running operations