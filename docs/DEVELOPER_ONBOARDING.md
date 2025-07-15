# Developer Onboarding Guide

Welcome to the Video Intelligence Platform! This guide will help you get up and running quickly.

## Table of Contents
- [Project Overview](#project-overview)
- [Environment Setup](#environment-setup)
- [Understanding the Codebase](#understanding-the-codebase)
- [Development Workflow](#development-workflow)
- [Your First Task](#your-first-task)
- [Key Commands](#key-commands)
- [Getting Help](#getting-help)
- [Common Issues](#common-issues)

## Project Overview

### What We're Building
A platform that transforms videos into searchable, conversational knowledge bases using:
- Multi-modal AI for video analysis
- Knowledge graphs for relationship mapping
- RAG (Retrieval-Augmented Generation) for intelligent Q&A
- Real-time conversational interface

### Architecture Philosophy
- **Two-Phase System**:
  1. **Ingestion Phase**: Heavy preprocessing (video analysis, knowledge extraction)
  2. **Runtime Phase**: Lightweight queries (semantic search, conversational AI)
- **Provider Abstraction**: Swap between AWS, NVIDIA, OpenAI seamlessly
- **Cost Optimization**: Smart caching, batching, and provider selection

### Tech Stack
- **Backend**: Python 3.11+, FastAPI, Celery
- **Database**: MongoDB (documents), Redis (cache/queue), Vector DB (embeddings)
- **AI/ML**: OpenAI, NVIDIA VILA, AWS Rekognition
- **Infrastructure**: Docker, AWS S3

## Environment Setup

### 1. Prerequisites Check
```bash
# Verify installations
python --version  # Should be 3.11+
docker --version
docker compose version
git --version
```

### 2. Clone and Setup
```bash
# Clone repository
git clone <repository-url>
cd video-intelligence-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Services
```bash
# Start MongoDB and Redis
docker compose up -d mongodb redis

# Verify services
docker compose ps
```

### 4. Initialize Project
```bash
# Set up project tracking
python scripts/init_project_status.py
python scripts/init_technical_debt.py

# Test knowledge base
./dev-cli ask "How does the project work?"
```

### 5. Environment Variables
Create `.env` file in project root:
```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017/video_intelligence

# Redis
REDIS_URL=redis://localhost:6379

# AWS (get from team)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your-input-bucket
S3_OUTPUT_BUCKET=your-output-bucket

# OpenAI (get from team)
OPENAI_API_KEY=your_key

# Optional: NVIDIA
NVIDIA_API_KEY=your_key
```

## Understanding the Codebase

### Directory Structure
```
video-intelligence-project/
├── services/backend/
│   ├── api/            # REST API endpoints
│   ├── workers/        # Async Celery tasks
│   ├── services/       # Business logic
│   │   ├── chunking/   # Video chunking
│   │   ├── analysis/   # Provider integrations
│   │   ├── knowledge_graph/  # Graph construction
│   │   ├── embeddings/       # Vector generation
│   │   └── rag/             # RAG implementation
│   ├── models/         # MongoDB schemas
│   ├── schemas/        # Pydantic models
│   ├── utils/          # Shared utilities
│   └── tests/          # Test suite
├── docs/               # Documentation
├── scripts/            # Management scripts
├── dev-knowledge-base/ # Development RAG
└── PROMPTS.md         # AI assistant guide
```

### Key Concepts

#### 1. MongoDB Models (Beanie ODM)
```python
# Example: Video model
from beanie import Document

class Video(Document):
    title: str
    s3_uri: str
    status: VideoStatus
    scenes: List[PydanticObjectId] = []
```

#### 2. Provider Pattern
```python
# All providers implement BaseAnalyzer
class NvidiaVilaAnalyzer(BaseAnalyzer):
    async def analyze_chunk(self, chunk, config):
        # Provider-specific analysis
        pass
```

#### 3. Celery Tasks
```python
@celery_app.task(bind=True)
def process_video(self, video_id: str):
    # Long-running async processing
    pass
```

#### 4. Caching Strategy
```python
@cache_api_call(service='nvidia_vila')
def expensive_analysis(params):
    # Automatically cached
    pass
```

## Development Workflow

### Daily Routine

#### 1. Start Your Day
```bash
# Activate environment
source venv/bin/activate

# Check project status
python scripts/init_project_status.py

# Check technical debt
python scripts/init_technical_debt.py | head -30

# See what needs doing
./dev-cli ask "What should I work on next?"
```

#### 2. Before Starting a Task
```bash
# Research the task
./dev-cli ask "How to implement [feature]"
./dev-cli ask "Any issues with [component]"

# Check for existing patterns
./dev-cli suggest "[component_name]"

# Look for reusable code
grep -r "similar_function" /path/to/VideoCommentator
```

#### 3. During Development
- Follow existing patterns (check similar files)
- Add technical debt items for incomplete work
- Write tests alongside code
- Use type hints and docstrings

#### 4. After Completing Work
```bash
# Run tests
pytest services/backend/tests/test_your_feature.py

# Update project status (edit then run)
python scripts/update_project_status.py

# Update technical debt if needed
python scripts/update_technical_debt.py

# Commit with clear message
git add .
git commit -m "feat: Add video chunking with overlap support"
```

### Code Style Guidelines

#### Python Style
- Use Black for formatting: `black services/`
- Type hints for all functions
- Docstrings for public methods
- Async/await for I/O operations

#### Example Function
```python
from typing import List, Optional
import structlog

logger = structlog.get_logger()

async def process_video_chunk(
    chunk_id: str,
    config: AnalysisConfig,
    providers: Optional[List[str]] = None
) -> AnalysisResult:
    """
    Process a video chunk with specified providers.
    
    Args:
        chunk_id: Unique identifier for the chunk
        config: Analysis configuration
        providers: List of provider names (default: all)
        
    Returns:
        AnalysisResult with aggregated provider outputs
        
    Raises:
        ProviderError: If all providers fail
    """
    logger.info("Processing chunk", chunk_id=chunk_id)
    # Implementation
```

## Your First Task

### Option 1: Fix a Low-Priority Technical Debt
```bash
# Find quick wins
python scripts/init_technical_debt.py | grep -B5 "LOW"

# Pick one marked as 1-2 hours
# Follow the resolution steps in docs/TECHNICAL_DEBT.md
```

### Option 2: Add Missing Tests
```bash
# Find untested code
pytest --cov=services.backend --cov-report=html
open htmlcov/index.html

# Pick a service with low coverage
# Write unit tests following existing patterns
```

### Option 3: Improve Documentation
- Add docstrings to undocumented functions
- Update API endpoint descriptions
- Create examples for complex features

## Key Commands

### Project Management
```bash
# Check status
python scripts/init_project_status.py
python scripts/init_technical_debt.py

# Query knowledge base
./dev-cli ask "your question"
./dev-cli suggest "component"

# Run specific tests
pytest -xvs services/backend/tests/test_file.py::test_function
```

### Docker Operations
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f mongodb
docker compose logs -f redis

# Reset database
docker compose down -v
docker compose up -d mongodb redis
```

### Development Tools
```bash
# Format code
black services/

# Type checking
mypy services/backend/

# Start API locally
cd services/backend
uvicorn main:app --reload

# Start Celery worker
celery -A celery_app worker --loglevel=info
```

## Getting Help

### 1. Internal Resources
- **Knowledge Base**: `./dev-cli ask "your question"`
- **Code Examples**: Search VideoCommentator repo
- **Documentation**: Check `docs/` directory
- **Tests**: Examples of how features should work

### 2. Key Documents
- [Project Management](./PROJECT_MANAGEMENT.md) - Tracking system
- [Technical Debt](./TECHNICAL_DEBT.md) - Known issues
- [PRD](./new/video-intelligence-prd.md) - Requirements
- [CLAUDE.md](../CLAUDE.md) - AI assistant guide

### 3. Debugging Tips
```python
# Add structured logging
import structlog
logger = structlog.get_logger()

logger.info("Processing video", 
    video_id=video_id,
    provider=provider_name,
    chunk_count=len(chunks)
)

# Use debugger
import pdb; pdb.set_trace()

# Print MongoDB queries
from mongoengine import QuerySet
QuerySet._debug = True
```

## Common Issues

### MongoDB Connection Failed
```bash
# Check if MongoDB is running
docker compose ps mongodb

# Restart if needed
docker compose restart mongodb

# Check logs
docker compose logs mongodb
```

### Import Errors
```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

### Celery Tasks Not Running
```bash
# Check Redis is running
docker compose ps redis

# Start worker manually
celery -A celery_app worker --loglevel=debug

# Check task registry
celery -A celery_app inspect registered
```

### Knowledge Base Issues
```bash
# Rebuild if needed
cd dev-knowledge-base
python ingestion/extract_knowledge.py

# Check ChromaDB
python -c "import chromadb; print(chromadb.__version__)"
```

## Next Steps

1. **Week 1**: 
   - Complete environment setup
   - Run existing tests
   - Fix one technical debt item
   - Read through PRD

2. **Week 2**:
   - Implement a small feature
   - Add comprehensive tests
   - Update documentation
   - Participate in code review

3. **Week 3**:
   - Take on a larger component
   - Integrate with existing services
   - Optimize performance
   - Share learnings

## Tips for Success

1. **Ask Questions**: Use the knowledge base liberally
2. **Follow Patterns**: Consistency is key
3. **Test Early**: Write tests as you code
4. **Document**: Future you will thank present you
5. **Track Progress**: Update project status regularly
6. **Learn from History**: VideoCommentator has solutions

Welcome to the team! 🚀