# CLAUDE.md - Video Intelligence Platform

This file provides guidance to Claude CLI when working with the Video Intelligence Platform codebase.

## Project Overview

This is a complete redesign of VideoCommentator, transforming it into a comprehensive Video Intelligence Platform with advanced knowledge memory capabilities using RAG/Graph-RAG technologies and MongoDB.

**Key Architecture**: Two-phase system
1. **Ingestion Phase**: Heavy preprocessing to extract comprehensive knowledge
2. **Runtime Phase**: Lightweight retrieval for real-time conversational AI

## Reference Repository

**Old VideoCommentator Repository**: `/Users/filip/Documents/Source/VideoCommentator-MonoRepo` 

Key patterns to reference from the old repository:
- Provider abstraction: `services/backend/services/video_analysis/`
- S3 utilities: `services/backend/services/s3_utils.py`
- Redis caching: `services/backend/utils/cache_utils.py`
- Celery configuration: `services/backend/celery_app.py`
- Docker patterns: `docker-compose.yml`

## Primary Documentation

1. **Product Requirements Document**: `docs/new/VIDEO_INTELLIGENCE_PRD.md`
   - Complete architecture specification
   - MongoDB schemas
   - API design
   - Implementation phases

2. **Development Knowledge Base**: `dev-knowledge-base/`
   - Query with: `./dev-cli ask "your question"`
   - Contains lessons learned, patterns, and decisions from VideoCommentator

3. **NVIDIA Blueprints**: `dev-knowledge-base/docs/pdfs/`
   - Multi-modal AI pipeline architecture
   - RAG implementation patterns
   - Knowledge graph construction

## Critical Patterns from VideoCommentator

### 1. Pydantic V2 Requirements
```python
# Always use these patterns:
from pydantic import BaseModel, field_validator, Field
from typing import Optional, List

class ExampleModel(BaseModel):
    field: str = Field(pattern="^[a-z]+$")  # Use 'pattern' not 'regex'
    
    @field_validator('field')
    @classmethod  # Always use @classmethod decorator
    def validate_field(cls, v, info):
        # Access field name via info.field_name
        return v
    
    # Use .model_dump() not .dict()
```

### 2. Provider Abstraction Pattern
```python
# Always use factory pattern for providers
from services.video_analysis.factory import ProviderFactory

provider = ProviderFactory.create_provider(provider_name)
# Never instantiate providers directly
```

### 3. Caching Strategy
```python
# Include project context in cache keys
cache_key = f"project:{project_id}:video:{video_id}:analysis"
# Separate shared vs project-specific caches
```

### 4. Celery Task Pattern
```python
@celery_app.task(bind=True, acks_late=True, max_retries=3)
def process_video(self, video_id: str):
    try:
        # Always update state
        self.update_state(state='PROGRESS', meta={'progress': 50})
        # Implementation
    except Exception as e:
        # Always include retry logic
        raise self.retry(exc=e, countdown=60)
```

## Development Workflow

### 1. Before implementing any component:
```bash
# Query the knowledge base for patterns
./dev-cli ask "How should I implement [component]?"
./dev-cli suggest "[component_name]"

# Generate context for Claude CLI
python tools/generate_claude_context.py "[topic]" > .claude/context.md
```

### 2. Follow this implementation order:
1. Check PRD for specifications
2. Query knowledge base for patterns
3. Reference old repository for working examples
4. Implement with test coverage
5. Update documentation

### 3. Key directories:
```
services/backend/
├── api/                    # FastAPI routes
├── workers/                # Celery tasks (use Canvas patterns)
├── services/               # Business logic
│   ├── chunking/          # Video segmentation
│   ├── analysis/          # Provider integrations
│   ├── knowledge_graph/   # Graph construction
│   ├── embeddings/        # Vector operations
│   └── rag/               # Retrieval system
├── models/                # MongoDB models (Beanie)
└── schemas/               # Pydantic schemas
```

## Implementation Guidelines

### API Development
- Use FastAPI with async/await
- All endpoints return Pydantic models
- Implement proper error handling with HTTPException
- Use dependency injection for services

### Database Patterns
- MongoDB with Beanie ODM for document storage
- Redis for caching and Celery broker
- Vector DB (Milvus/Pinecone) for embeddings
- Always use connection pooling

### Video Processing
- Start with AWS Rekognition for shot detection
- Process in parallel using Celery group/chord
- Store artifacts in S3 with consistent naming
- Cache aggressively at every layer

### Testing Requirements
- Unit tests for all services
- Integration tests for API endpoints
- Mock external services (AWS, OpenAI)
- Use pytest fixtures for common setups

## Common Pitfalls to Avoid

1. **Memory Issues**: Set worker limits
   ```python
   worker_max_memory_per_child=2048000  # 2GB
   ```

2. **S3 Path Validation**: Always validate S3 URIs before using cached data

3. **Provider Costs**: Track and optimize - AWS: $0.001/frame, NVIDIA: $0.0035/frame

4. **Task Timeouts**: Set appropriate limits
   ```python
   task_time_limit=3600  # 1 hour
   task_soft_time_limit=3000  # 50 minutes
   ```

## Environment Variables

Required variables (see `.env.example`):
- `MONGODB_URL`
- `REDIS_URL`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET`, `S3_OUTPUT_BUCKET`
- `OPENAI_API_KEY`
- `NVIDIA_API_KEY` (optional)
- `VECTOR_DB_TYPE` (milvus or pinecone)

## Quick Commands

```bash
# Start development environment
docker compose up -d
source venv/bin/activate

# Run tests
pytest services/backend/tests/

# Check implementation patterns
./dev-cli ask "What's the pattern for [topic]?"

# Generate API documentation
cd services/backend && python -m api.generate_docs
```

## When in Doubt

1. Check the PRD: `docs/new/VIDEO_INTELLIGENCE_PRD.md`
2. Query knowledge base: `./dev-cli ask "[question]"`
3. Reference old code: Look in `/Users/filip/Documents/Source/VideoCommentator-MonoRepo` 
4. Follow NVIDIA blueprints: Check PDFs in knowledge base

Remember: This project demonstrates its own capabilities - we're using RAG to build a RAG system!
