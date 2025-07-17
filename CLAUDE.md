# CLAUDE.md - Video Intelligence Platform

This file provides guidance to Claude CLI when working with the Video Intelligence Platform codebase.

## Project Overview

This is a comprehensive Video Intelligence Platform with advanced knowledge memory capabilities using RAG/Graph-RAG technologies and MongoDB.

**Key Architecture**: Two-phase system
1. **Ingestion Phase**: Heavy preprocessing to extract comprehensive knowledge
2. **Runtime Phase**: Lightweight retrieval for real-time conversational AI

## Prompt Templates

**IMPORTANT**: Prompts are now organized in `.claude/prompts/` directory. You can:

1. **Reference prompts directly**:
   ```
   Use the prompt from .claude/prompts/project-management/status-check.md
   ```

2. **Execute prompts programmatically**:
   ```
   python scripts/prompt.py exec status-check
   ```

3. **View available prompts**:
   ```
   python scripts/prompt.py list
   ```

### Key Prompts:
- **Project Management**: status-check, status-update, next-task
- **Technical Debt**: debt-check, debt-add, debt-resolve
- **Development**: impl-plan, feature, bug, test
- **Knowledge Base**: knowledge-query, knowledge-add
- **Workflows**: common-workflows

For detailed prompt documentation, see `.claude/README.md`

## Key Architecture Patterns

- Provider abstraction pattern for video analysis
- S3 utilities for cloud storage
- Redis caching for performance
- Celery for distributed task processing
- Docker-based development environment

## Primary Documentation

1. **Product Requirements Document**: `docs/new/video-intelligence-prd.md`
   - Complete architecture specification
   - MongoDB schemas
   - API design
   - Implementation phases

2. **Development Knowledge Base**: `dev-knowledge-base/`
   - Query with: `./dev-cli ask "your question"`
   - Contains architecture patterns, best practices, and implementation guidelines

3. **NVIDIA Blueprints**: `dev-knowledge-base/docs/pdfs/`
   - Multi-modal AI pipeline architecture
   - RAG implementation patterns
   - Knowledge graph construction

## Critical Implementation Patterns

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

## Graph-RAG Knowledge System

### Architecture
- **Qdrant**: Vector search for semantic similarity (224+ documents indexed)
- **Neo4j**: Graph relationships between concepts
- **MongoDB**: Persistent storage

### MANDATORY Usage in Development
**IMPORTANT**: You MUST use Graph-RAG before implementing ANY component:

1. **Search for patterns** (ALWAYS DO THIS FIRST):
   ```bash
   ./dev-cli search "[component] implementation patterns"
   ./dev-cli search "NVIDIA Blueprint [component]"
   ./dev-cli search "[component] best practices"
   ```

2. **Explore technology relationships**:
   ```bash
   ./dev-cli explore "[main technology]" --depth 2
   ./dev-cli explore "[component]" --depth 3
   ```

3. **Ask specific questions**:
   ```bash
   ./dev-cli ask "How should I implement [component]?"
   ./dev-cli ask "What are the cost implications of [approach]?"
   ```

4. **Check knowledge base status**:
   ```bash
   ./dev-cli info  # Shows indexed documents and entities
   ```

### Query Patterns
- **Implementation**: `search "video chunking implementation"`
- **Debugging**: `search "[error message]"`
- **Optimization**: `search "cost optimization [component]"`
- **Architecture**: `search "two-phase pipeline patterns"`

## Development Workflow

### 1. Before implementing any component:
```bash
# MANDATORY: Query Graph-RAG for patterns
./dev-cli search "[component] implementation patterns"
./dev-cli search "NVIDIA Blueprint [component]"
./dev-cli explore "[main technology]" --depth 2

# Ask specific implementation questions
./dev-cli ask "How should I implement [component]?"
./dev-cli suggest "[component_name]"

# Generate context if needed
python tools/generate_claude_context.py "[topic]" > .claude/context.md
```

### 2. Follow this implementation order:
1. **Query Graph-RAG first** (non-negotiable)
2. Check PRD for specifications
3. Apply NVIDIA Blueprint patterns found
4. Implement with test coverage
5. Update documentation and knowledge base

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

1. **Not Using Graph-RAG**: ALWAYS search knowledge base before implementing
   ```bash
   # BAD: Implementing without checking
   # GOOD: ./dev-cli search "component patterns" first
   ```

2. **Memory Issues**: Set worker limits
   ```python
   worker_max_memory_per_child=2048000  # 2GB
   ```

3. **S3 Path Validation**: Always validate S3 URIs before using cached data

4. **Provider Costs**: Track and optimize - AWS: $0.001/frame, NVIDIA: $0.0035/frame

5. **Task Timeouts**: Set appropriate limits
   ```python
   task_time_limit=3600  # 1 hour
   task_soft_time_limit=3000  # 50 minutes
   ```

6. **Ignoring NVIDIA Blueprints**: These are proven patterns - use them!

## Environment Variables

Required variables (see `.env.example`):
- `MONGODB_URL`
- `REDIS_URL`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET`, `S3_OUTPUT_BUCKET`
- `OPENAI_API_KEY`
- `NVIDIA_API_KEY` (optional)
- `VECTOR_DB_TYPE` (qdrant)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` (for Graph-RAG)

## Docker Development Environment

### Starting the Environment
```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f [service_name]

# Stop services
docker compose down
```

### Services and Ports
- **API (FastAPI)**: http://localhost:8003
  - Health: http://localhost:8003/health
  - Docs: http://localhost:8003/api/docs
  - OpenAPI: http://localhost:8003/api/v1/openapi.json
- **MongoDB**: localhost:27017
  - Database: video-intelligence
  - Collections: project_status, technical_debt, videos, analyses, etc.
- **Redis**: localhost:6379
  - Used for Celery broker and result backend
- **Qdrant**: http://localhost:6333
  - Dashboard: http://localhost:6333/dashboard
  - Collections: nvidia_blueprints (1,167 vectors)
- **Neo4j**: http://localhost:7474
  - Browser UI: http://localhost:7474
  - Bolt protocol: localhost:7687
  - Default auth: neo4j/password123
- **Celery Worker**: Running with 4 threads
  - Configured for video processing tasks
- **Flower**: http://localhost:5555 (currently disabled due to import issues)

### Important Notes
- All Python imports must be absolute (no relative imports with ..)
- PYTHONPATH is set to /services/backend in containers
- FFmpeg is installed for video processing
- Use real AWS S3 buckets via environment variables

### Common Issues and Fixes
1. **Import Errors**: Ensure all imports are absolute
2. **Port Conflicts**: Ensure no conflicting services are running
3. **Missing Dependencies**: Add to requirements.txt and rebuild
4. **Class Name Mismatches**: Check actual class names in files
5. **Docker Service Health Check Failures**: 
   - Neo4j/Qdrant: Changed from `service_healthy` to `service_started` in depends_on
   - Fixed health check commands for proper URL format
6. **ModuleNotFoundError with dev-cli**: Use the wrapper script `./dev-cli` from project root

## Quick Commands

```bash
# Start development environment
docker compose up -d

# MANDATORY before implementing anything
./dev-cli search "[component] implementation patterns"
./dev-cli explore "[technology]" --depth 2

# Run tests in container
docker compose exec api pytest

# Execute Python scripts
docker compose exec api python /services/backend/scripts/script_name.py

# Access container shell
docker compose exec api bash

# Rebuild after requirements change
docker compose build --no-cache

# Check implementation patterns (use search instead of ask)
./dev-cli search "pattern for [topic]"
./dev-cli info  # Check knowledge base status
```

## Recent Updates (July 2025)

### Graph-RAG Knowledge System (COMPLETED)
- ✅ Migrated from ChromaDB to Qdrant + Neo4j
- ✅ 1,167 documents indexed from NVIDIA Blueprints and project docs
- ✅ Graph relationships for technology connections
- ✅ Enhanced CLI with search and explore commands
- ✅ All prompts updated for Graph-RAG integration
- ✅ Dev-cli wrapper script for easy access from project root

### Docker Infrastructure (COMPLETED)
- ✅ Full Docker setup with docker-compose.yml
- ✅ Production-ready Dockerfile with FFmpeg
- ✅ GitHub Actions for AWS ECS deployment
- ✅ Open source friendly (no hardcoded secrets)
- ✅ Comprehensive deployment documentation
- ✅ All services running and tested locally
- ✅ Health checks fixed for Neo4j and Qdrant

### MongoDB Initialization (COMPLETED)
- ✅ ProjectStatus model tracking development progress
- ✅ TechnicalDebt model for tracking issues
- ✅ Initialization script at `scripts/initialize_project_status.py`
- ✅ Current phase: KNOWLEDGE_BUILDING
- ✅ Component statuses tracked

### Known Issues
- Flower monitoring UI has import errors (disabled) - Low priority
- No automated tests for Docker setup yet
- Authentication system missing - CRITICAL

### Next Priority Tasks
1. Implement authentication system (CRITICAL)
2. Create comprehensive test suite
3. Implement video chunking with FFmpeg
4. AWS Rekognition provider integration
5. S3 integration for video storage

## When in Doubt

1. **FIRST**: Search Graph-RAG: `./dev-cli search "[topic]"`
2. **THEN**: Explore relationships: `./dev-cli explore "[technology]" --depth 2`
3. Check the PRD: `docs/new/video-intelligence-prd.md`
4. Follow NVIDIA blueprints (indexed in knowledge base)
5. Check deployment docs: `docs/deployment/`

Remember: This project demonstrates its own capabilities - we're using Graph-RAG to build a video intelligence system with Graph-RAG!

## Graph-RAG Best Practices

1. **Always search before implementing**:
   ```bash
   ./dev-cli search "video chunking patterns"  # Do this
   # NOT: Just start coding based on assumptions
   ```

2. **Use entity exploration for technology decisions**:
   ```bash
   ./dev-cli explore "Celery" --depth 2  # See all related patterns
   ```

3. **Combine search and ask**:
   ```bash
   ./dev-cli search "cost optimization"  # Find relevant docs
   ./dev-cli ask "How to reduce inference costs?"  # Get specific answer
   ```

4. **Check knowledge coverage**:
   ```bash
   ./dev-cli info  # See what's indexed
   ```

## Using Prompt Templates

Always use the templates in PROMPTS.md for consistency and ensure Python environment (source venv/bin/activate) is running at root of the project.
Common workflows:

### Starting a Session
```
Apply the status-check template from PROMPTS.md
```

### Implementing Features
```
Use the impl-plan template to implement video chunking service
```

### Getting Next Task
```
Apply the next-task template to see what to work on
```

### Updating Progress
```
Use the status-update template after completing the chunking service
```

### Debugging
```
Apply the bug template for the MongoDB connection issue
```

The templates ensure you:
- Always check the knowledge base first
- Update MongoDB status tracking
- Follow PRD specifications
- Document new patterns
- Test properly
