# Video Ingestion Architecture

## Overview
The video ingestion phase implements a comprehensive preprocessing pipeline that extracts all possible information from videos for efficient runtime retrieval.

## Key Design Decisions

### 1. Fixed-Duration Chunking
- **Decision**: Use fixed-duration chunks (15-30 seconds) instead of shot-based chunking
- **Rationale**: 
  - Predictable processing costs and timing
  - Better compatibility with model constraints
  - Simpler implementation and debugging
- **Model-Specific Defaults**:
  - AWS Rekognition: 30 seconds (processes full segments well)
  - NVIDIA VILA: 20 seconds (optimal for frame analysis)
  - OpenAI GPT-4V: 15 seconds (token efficiency)

### 2. Timestamp Extraction vs Chunking
- **AWS Rekognition**: Used for extracting interesting timestamps (shots, objects, scenes) NOT for determining chunk boundaries
- **NVIDIA VILA**: Used for prompt-based analysis of specific moments
- **Benefit**: Rich temporal markers for navigation without complex chunking logic

### 3. Video Memory System
The `VideoMemory` model serves as the bridge between ingestion and runtime phases:

```python
VideoMemory:
  - chunks: List of chunk data with transcripts and embeddings
  - temporal_markers: Timestamps of interest (scene changes, objects, etc.)
  - full_transcript: Complete time-aligned transcript
  - aggregated data: Unique objects, scene descriptions, etc.
```

## Implementation Architecture

### Components
1. **VideoChunker**: FFmpeg-based fixed-duration chunking with S3 upload
2. **AnalysisPlanner**: Determines chunk duration and provider selection
3. **ProviderOrchestrator**: Manages parallel analysis across providers
4. **OrchestrationService**: Coordinates the entire pipeline and builds memory

### Data Flow
```
Video Upload → Fixed Chunking → Parallel Analysis:
                                ├─ Visual Analysis (AWS/NVIDIA)
                                ├─ Audio Transcription (AWS/NVIDIA)
                                └─ Custom Analysis
                                → Memory Building
                                → MongoDB Storage
```

## Key Patterns

### 1. Async Processing with Celery
```python
# API triggers Celery task
task = process_video_ingestion.apply_async(
    args=[job_id, video_id, user_prompt],
    queue='orchestration'
)

# Celery task uses orchestration service
result = await orchestration_service.process_video(
    video_id=video_id,
    user_prompt=user_prompt,
    processing_job_id=job_id
)
```

### 2. Provider-Specific Configuration
```python
# In AnalysisPlanner._determine_chunk_settings()
if ProviderType.AWS_REKOGNITION in all_providers:
    chunk_duration = 30
elif ProviderType.NVIDIA_VILA in all_providers:
    chunk_duration = 20
```

### 3. Memory Building Pattern
```python
# Build comprehensive memory from all results
video_memory = VideoMemory(
    chunks=[...],  # Chunk-level data
    temporal_markers=[...],  # Interesting timestamps
    full_transcript=...,  # Aggregated transcript
    # Rich metadata for search
)
```

## Technical Debt Identified

1. **Missing Error Handling**: Need better handling for provider failures
2. **No Retry Logic**: Failed chunks should be retryable individually
3. **Missing Embeddings**: Chunks need embeddings for semantic search
4. **No Integration Tests**: Full pipeline needs end-to-end tests

## Cost Optimization

- **Transcription Costs**:
  - AWS Transcribe: $0.024/minute (~$1.44/hour)
  - NVIDIA Riva: ~$0.02/minute (GPU-based, better for volume)
- **Strategy**: Start with AWS, evaluate Riva for scale

## Next Steps

1. Implement AWS Rekognition for timestamp extraction
2. Add NVIDIA VILA for prompt-based analysis
3. Integrate transcription services
4. Add embedding generation
5. Create comprehensive tests