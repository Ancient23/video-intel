# Knowledge Sources Manifest

This file maintains a comprehensive list of all knowledge sources for the Video Intelligence Platform's Graph-RAG system. Update this file whenever adding new sources.

Last Updated: 2025-07-17

## PDF Documents

### Local PDFs
These PDFs are already in the repository and should be processed:

- `/research/NVIDIA-Powered Architecture for Video Understanding and Conversational AI.pdf`
  - Core architecture patterns for video intelligence
  - Two-phase pipeline design (ingestion + retrieval)
  
- `/research/Multi‑Modal AI Pipeline_ NVIDIA Blueprint vs. Custom Solutions (Q&A).pdf`
  - Comparison of approaches
  - Best practices for multi-modal analysis

### External PDF Resources to Add
These PDFs should be downloaded and added to the knowledge base:

- **AWS Rekognition Video Documentation PDF**
  - Video analysis API patterns
  - Shot detection and scene analysis
  
- **Celery Canvas Patterns Guide**
  - Distributed task orchestration
  - Video processing pipeline patterns
  
- **FFmpeg Video Processing Best Practices**
  - Efficient video chunking
  - Codec optimization for ML

## GitHub Repositories

### NVIDIA AI Blueprints (Primary Sources)

1. **Video Search and Summarization** ⭐ CRITICAL
   - URL: https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization
   - Purpose: Core 2-phase ingestion/retrieval pipeline architecture
   - Key Files: 
     - `/docs/` - All documentation
     - `/src/` - Implementation examples
     - `README.md` - Architecture overview
   - Extract: Pipeline stages, service architecture, deployment patterns

2. **Digital Human**
   - URL: https://github.com/NVIDIA-AI-Blueprints/digital-human
   - Purpose: Retrieval phase conversational AI patterns
   - Key Files:
     - `/avatar/` - Avatar interface implementations
     - `/chat/` - Conversational patterns
     - `/docs/` - Integration guides
   - Extract: Real-time chat patterns, avatar integration

3. **Data Flywheel**
   - URL: https://github.com/NVIDIA-AI-Blueprints/data-flywheel
   - Purpose: Cost optimization using NeMo microservice
   - Key Files:
     - `/docs/02-quickstart.md` - Implementation guide
     - `/nemo/` - NeMo integration patterns
     - `/optimization/` - Cost reduction strategies
   - Extract: Inference caching, model optimization, cost patterns

4. **RAG Pipeline**
   - URL: https://github.com/NVIDIA-AI-Blueprints/rag
   - Purpose: RAG implementation patterns
   - Key Files: All documentation and examples
   - Extract: Retrieval patterns, embedding strategies

### Video Processing & ML Libraries

1. **Open CLIP**
   - URL: https://github.com/mlfoundations/open_clip
   - Purpose: Vision-language models for video understanding
   - Key Files: `/docs/`, `/src/training/`, model cards
   - Extract: Multi-modal embedding patterns

2. **LLaVA**
   - URL: https://github.com/haotian-liu/LLaVA
   - Purpose: Visual instruction tuning
   - Key Files: `/llava/`, `/docs/`, training guides
   - Extract: Visual QA patterns, fine-tuning strategies

3. **Qdrant**
   - URL: https://github.com/qdrant/qdrant
   - Purpose: Vector database implementation
   - Key Files: `/lib/collection/`, `/docs/`
   - Extract: Collection management, search optimization

4. **Neo4j**
   - URL: https://github.com/neo4j/neo4j
   - Purpose: Graph database patterns
   - Key Files: `/community/cypher/`, `/docs/`
   - Extract: Graph modeling, Cypher patterns

### Infrastructure & Best Practices

1. **Celery**
   - URL: https://github.com/celery/celery
   - Purpose: Distributed task queue patterns
   - Key Files: 
     - `/docs/userguide/canvas.rst` - Canvas patterns
     - `/celery/canvas/` - Implementation
   - Extract: Task orchestration, error handling, retries

2. **AWS SDK Python (Boto3)**
   - URL: https://github.com/boto/boto3
   - Purpose: AWS service integration
   - Key Files:
     - `/boto3/docs/` - Service documentation
     - `/examples/` - Integration examples
   - Extract: S3 patterns, Rekognition usage

3. **FFmpeg**
   - URL: https://github.com/FFmpeg/FFmpeg
   - Purpose: Video processing
   - Key Files: `/doc/`, `/libavcodec/`, `/libavformat/`
   - Extract: Video chunking, codec selection, streaming

4. **FastAPI**
   - URL: https://github.com/tiangolo/fastapi
   - Purpose: Async API patterns
   - Key Files: `/docs/`, `/fastapi/`, async patterns
   - Extract: Async/await patterns, dependency injection

5. **httpx**
   - URL: https://github.com/encode/httpx
   - Purpose: Async HTTP client patterns
   - Key Files: `/docs/`, `/httpx/`
   - Extract: Async request patterns, connection pooling

6. **Beanie**
   - URL: https://github.com/roman-right/beanie
   - Purpose: MongoDB ODM patterns
   - Key Files: `/docs/`, `/beanie/`
   - Extract: Document modeling, async queries

## Web Resources

### Architecture & Patterns
1. **Graph-RAG with Qdrant and Neo4j**
   - URL: https://qdrant.tech/documentation/examples/graphrag-qdrant-neo4j/
   - Purpose: Graph-RAG implementation guide
   - Extract: Integration patterns, query optimization

2. **AWS Rekognition Video Documentation**
   - URL: https://docs.aws.amazon.com/rekognition/latest/dg/video.html
   - Purpose: Video analysis service patterns
   - Extract: API usage, cost optimization, limitations

3. **Celery Canvas Documentation**
   - URL: https://docs.celeryq.dev/en/stable/userguide/canvas.html
   - Purpose: Complex workflow patterns
   - Extract: Groups, chains, chords for video processing

4. **FFmpeg Documentation**
   - URL: https://ffmpeg.org/documentation.html
   - Purpose: Video processing reference
   - Extract: Command patterns, filter graphs

### Best Practices Guides
1. **MongoDB Aggregation Pipelines**
   - URL: https://www.mongodb.com/docs/manual/aggregation/
   - Purpose: Complex query patterns
   - Extract: Video timeline queries, performance tips

2. **Redis Caching Strategies**
   - URL: https://redis.io/docs/manual/patterns/
   - Purpose: Caching patterns for video metadata
   - Extract: Cache invalidation, TTL strategies

3. **S3 Multipart Upload**
   - URL: https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html
   - Purpose: Large video file handling
   - Extract: Upload strategies, error recovery

4. **ML Cost Optimization**
   - URL: https://aws.amazon.com/blogs/machine-learning/
   - Purpose: Reducing inference costs
   - Extract: Batch processing, model optimization

## Internal Documentation

### Project Documentation
- `/docs/new/video-intelligence-prd.md` - Product requirements and architecture
- `/CLAUDE.md` - Development guidelines and patterns
- `/README.md` - Project overview
- `/docs/graph-rag-setup.md` - Graph-RAG implementation guide

### Code Patterns to Extract
Extract patterns from these internal directories:
- `/services/backend/api/` - API endpoint patterns
- `/services/backend/services/` - Service layer patterns
- `/services/backend/workers/` - Celery task patterns
- `/services/backend/models/` - MongoDB schema patterns
- `/services/backend/schemas/` - Pydantic validation patterns

## Knowledge Extraction Strategy

### Priority Levels
1. **🔴 CRITICAL**: NVIDIA Blueprints (video-search-and-summarization)
2. **🟠 HIGH**: Infrastructure repos (Celery, AWS, FFmpeg)
3. **🟡 MEDIUM**: ML libraries (Open CLIP, LLaVA)
4. **🟢 LOW**: General best practices

### Entity Types to Extract
- **Technologies**: Qdrant, Neo4j, MongoDB, Redis, S3, etc.
- **Patterns**: Two-phase pipeline, Canvas workflows, caching strategies
- **Services**: AWS Rekognition, OpenAI, NVIDIA APIs
- **Concepts**: Graph-RAG, embeddings, video chunking, cost optimization

### Relationship Types
- `IMPLEMENTS` - Code that implements a pattern
- `OPTIMIZES` - Cost/performance optimization techniques  
- `DEPENDS_ON` - Service dependencies
- `ALTERNATIVE_TO` - Alternative approaches
- `USES` - Technology usage relationships
- `PART_OF` - Component relationships

## Maintenance

### Weekly Updates
- Check NVIDIA Blueprints for updates
- Review new AWS service features
- Update cost optimization strategies
- Add newly discovered patterns

### Addition Process
When adding new sources:
1. Add entry to appropriate section above
2. Include URL, purpose, and key files
3. Run population script: `python scripts/populate_knowledge_graph.py`
4. Verify with: `./dev-cli info`

### Quality Checks
- Ensure all URLs are valid
- Verify key files exist in repos
- Test extraction produces useful knowledge
- Check for duplicate sources