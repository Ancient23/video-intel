# Video Intelligence Platform - Claude CLI Instructions

## Project Overview

You are helping build a Video Intelligence Platform that transforms videos into searchable, conversational knowledge bases. This is a complete architectural redesign of the VideoCommentator project, focusing on:

1. **Pre-processing Phase**: Extract comprehensive knowledge from videos using multiple AI providers
2. **Runtime Phase**: Enable real-time conversational AI during video playback using pre-computed artifacts

## Reference Repository

The previous implementation is located at: `[OLD_REPO_PATH]`

**Important files to reference from the old repository:**
- `services/backend/services/video_analysis/` - Provider abstraction pattern
- `services/backend/services/s3_utils.py` - S3 utilities
- `services/backend/utils/cache_utils.py` - Redis caching patterns
- `services/backend/utils/mux.py` - FFmpeg integration
- `services/backend/celery_app.py` - Celery configuration
- `docker-compose.yml` - Docker setup patterns

## Architecture Summary

### Core Technologies
- **Backend**: FastAPI + Celery for async processing
- **Databases**: MongoDB (document store + graph), Redis (cache), Vector DB (Milvus/Pinecone)
- **AI/ML**: LangChain for orchestration, multiple video analysis providers
- **Deployment**: AWS ECS Fargate, S3, CloudFront

### Key Architectural Decisions
1. **Two-Phase System**: Heavy preprocessing, lightweight runtime
2. **Plugin Architecture**: Support any AI model/provider
3. **Knowledge Graph**: MongoDB for structured relationships
4. **Vector Search**: For semantic queries over video content
5. **MCP Server**: Standardized tool interface

## Implementation Instructions

### Phase 1: Project Setup

1. **Initialize the project structure:**
```bash
video-intelligence-platform/
├── services/
│   ├── backend/
│   │   ├── api/                    # FastAPI application
│   │   ├── workers/                # Celery workers
│   │   ├── core/                   # Core business logic
│   │   ├── services/               # Service layer
│   │   ├── models/                 # Data models
│   │   ├── schemas/                # Pydantic schemas
│   │   └── tests/                  # Test suite
│   └── mcp/                        # MCP server
├── infrastructure/                 # AWS CDK/Terraform
├── docker/                         # Docker configurations
├── scripts/                        # Utility scripts
└── docs/                          # Documentation
```

2. **Set up core dependencies:**
```python
# requirements.txt
fastapi==0.104.1
celery==5.3.4
redis==5.0.1
motor==3.3.2  # MongoDB async driver
pymongo==4.6.1
langchain==0.1.0
langchain-openai==0.0.5
pydantic==2.5.3
httpx==0.26.0
boto3==1.34.34
structlog==24.1.0
python-multipart==0.0.6
websockets==12.0
```

3. **Create the configuration system:**
```python
# services/backend/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "video-intelligence-platform"
    environment: str = "development"
    
    # MongoDB
    mongodb_url: str
    mongodb_database: str = "video_intelligence"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # S3
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    s3_bucket: str
    s3_output_bucket: str
    
    # AI Providers
    openai_api_key: str | None = None
    nvidia_api_key: str | None = None
    anthropic_api_key: str | None = None
    
    # Vector DB
    vector_db_type: str = "milvus"  # or "pinecone"
    milvus_host: str | None = None
    pinecone_api_key: str | None = None
    
    class Config:
        env_file = ".env"
```

### Phase 2: Video Processing Pipeline

1. **Implement video chunking service:**
```python
# services/backend/services/chunking/video_chunker.py
# Reference OLD_REPO_PATH/services/backend/tasks/video_tasks.py for video handling patterns

class VideoChunker:
    """
    Splits videos into analyzable chunks based on:
    - Shot boundaries (using AWS Rekognition)
    - Fixed time intervals
    - Scene changes
    """
    
    async def chunk_video(self, video_s3_uri: str, strategy: str = "shots") -> List[VideoChunk]:
        # Implementation here
        pass
```

2. **Create provider plugin system:**
```python
# services/backend/services/analysis/base_analyzer.py
# Extend pattern from OLD_REPO_PATH/services/backend/services/video_analysis/base.py

from abc import ABC, abstractmethod

class VideoAnalysisProvider(ABC):
    """Base class for all video analysis providers"""
    
    @abstractmethod
    async def analyze_chunk(self, chunk: VideoChunk) -> ChunkAnalysis:
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        pass
    
    @abstractmethod
    def estimate_cost(self, duration_seconds: float) -> float:
        pass
```

3. **Set up MongoDB models:**
```python
# services/backend/models/video_models.py
from datetime import datetime
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie

class VideoScene(Document):
    video_id: str
    scene_number: int
    start_time: float
    end_time: float
    shots: List[Dict[str, Any]]
    summary: str
    themes: List[str]
    mood: str
    graph_nodes: List[str]  # References to graph nodes
    
    class Settings:
        name = "video_scenes"

class KnowledgeGraphNode(Document):
    video_id: str
    node_type: str  # "entity", "event", "relationship"
    label: str
    properties: Dict[str, Any]
    embeddings: List[float]
    temporal_range: Dict[str, float]
    connections: List[Dict[str, Any]]
    
    class Settings:
        name = "knowledge_graph"
```

### Phase 3: Knowledge Graph Construction

1. **Implement graph builder:**
```python
# services/backend/services/knowledge_graph/graph_builder.py
class GraphBuilder:
    """
    Constructs knowledge graph from video analysis results
    Uses LangChain for entity extraction and relationship mapping
    """
    
    async def build_graph(self, video_id: str, analysis_results: List[ChunkAnalysis]) -> KnowledgeGraph:
        # Extract entities from each chunk
        # Map relationships between entities
        # Create temporal index
        # Store in MongoDB
        pass
```

2. **Create embedding service:**
```python
# services/backend/services/embeddings/embedding_generator.py
# Use patterns from OLD_REPO_PATH/services/backend/services/ai_tools.py

class EmbeddingService:
    """Generates embeddings for text, images, and video chunks"""
    
    async def generate_text_embedding(self, text: str) -> List[float]:
        pass
    
    async def generate_image_embedding(self, image_url: str) -> List[float]:
        pass
```

### Phase 4: RAG Implementation

1. **Build retrieval system:**
```python
# services/backend/services/rag/retriever.py
class VideoRetriever:
    """
    Retrieves relevant content based on:
    - Semantic similarity (vector search)
    - Temporal proximity (current playback time)
    - Graph relationships
    """
    
    async def retrieve(
        self, 
        query: str, 
        video_id: str, 
        timestamp: float,
        k: int = 5
    ) -> List[RetrievalResult]:
        pass
```

2. **Implement conversation engine:**
```python
# services/backend/services/conversation/chat_manager.py
class ConversationManager:
    """
    Manages conversation state and generates responses
    Uses LangChain for context-aware generation
    """
    
    async def create_conversation(self, video_id: str, persona: str) -> Conversation:
        pass
    
    async def generate_response(
        self, 
        conversation_id: str, 
        user_message: str,
        current_timestamp: float
    ) -> ChatResponse:
        pass
```

### Phase 5: API Implementation

1. **Create FastAPI routes:**
```python
# services/backend/api/routes/video_routes.py
from fastapi import APIRouter, UploadFile, BackgroundTasks

router = APIRouter(prefix="/api/v1/videos")

@router.post("/upload")
async def upload_video(file: UploadFile, background_tasks: BackgroundTasks):
    """Upload video and trigger processing"""
    # Reference OLD_REPO_PATH/services/backend/routes/s3_routes.py for S3 patterns
    pass

@router.post("/{video_id}/process")
async def process_video(video_id: str, providers: List[str]):
    """Start video processing with selected providers"""
    # Use Celery pattern from OLD_REPO_PATH/services/backend/tasks/orchestration_tasks.py
    pass
```

2. **Add WebSocket support:**
```python
# services/backend/api/websocket/conversation_ws.py
from fastapi import WebSocket

class ConversationWebSocket:
    async def handle_connection(self, websocket: WebSocket, conversation_id: str):
        """Handle real-time conversation streaming"""
        pass
```

### Phase 6: Celery Workflows

1. **Define Canvas workflows:**
```python
# services/backend/workers/workflows.py
from celery import group, chain, chord

def create_video_processing_workflow(video_id: str, providers: List[str]):
    """
    Creates Celery Canvas workflow for video processing
    Reference OLD_REPO_PATH/services/backend/celery_app.py for configuration
    """
    
    # Phase 1: Preprocessing
    preprocessing = chain(
        extract_video_metadata.s(video_id),
        chunk_video.s(),
        extract_audio.s()
    )
    
    # Phase 2: Parallel analysis per provider
    analysis_tasks = group([
        analyze_with_provider.s(provider) 
        for provider in providers
    ])
    
    # Phase 3: Knowledge building
    knowledge_building = chain(
        merge_analysis_results.s(),
        build_knowledge_graph.s(),
        generate_embeddings.s(),
        index_in_vector_db.s()
    )
    
    # Combine all phases
    workflow = chain(
        preprocessing,
        analysis_tasks,
        knowledge_building
    )
    
    return workflow
```

### Phase 7: MCP Server Implementation

1. **Create MCP server:**
```python
# services/mcp/server.py
class VideoIntelligenceMCPServer:
    """
    Model Context Protocol server for video intelligence tools
    """
    
    async def list_tools(self) -> List[MCPTool]:
        pass
    
    async def execute_tool(self, tool_name: str, params: Dict) -> Any:
        pass
```

## Testing Strategy

1. **Unit Tests**: Test each service in isolation
2. **Integration Tests**: Test provider integrations
3. **End-to-End Tests**: Test full video processing pipeline
4. **Load Tests**: Ensure system handles concurrent processing

Reference test patterns from `OLD_REPO_PATH/services/backend/tests/`

## Deployment Instructions

1. **Docker Setup:**
```dockerfile
# Reference OLD_REPO_PATH/services/backend/Dockerfile
# Adapt for new service structure
```

2. **AWS Infrastructure:**
- Use ECS Fargate for API and workers
- Set up MongoDB Atlas cluster
- Configure S3 buckets with lifecycle policies
- Set up CloudFront for CDN

## Key Implementation Notes

1. **Provider Costs**: Track and optimize costs per provider
2. **Caching**: Implement aggressive caching at all layers
3. **Error Handling**: Design for partial failures
4. **Monitoring**: Add comprehensive logging and metrics

## Migration from Old System

When implementing, reference these specific patterns from the old repository:

1. **S3 Operations**: Copy presigned URL generation logic
2. **Redis Caching**: Reuse cache key patterns and TTL strategies
3. **Provider Factory**: Extend the existing factory pattern
4. **Error Handling**: Copy retry and backoff strategies
5. **Docker Configuration**: Adapt docker-compose patterns

## Development Workflow

1. Start with MongoDB and basic CRUD operations
2. Implement video chunking and S3 storage
3. Add one provider (AWS Rekognition) as reference
4. Build knowledge graph construction
5. Implement basic RAG retrieval
6. Add API endpoints
7. Implement WebSocket support
8. Add remaining providers
9. Optimize and test

## Questions to Resolve

1. Which vector database? (Milvus vs Pinecone)
2. Primary LLM provider? (OpenAI vs Anthropic)
3. Graph query language? (MongoDB aggregation vs Neo4j Cypher)
4. Streaming protocol? (WebSocket vs Server-Sent Events)
5. Authentication method? (JWT vs OAuth2)

## Success Criteria

- Process 1-hour video in < 2 hours
- Generate responses in < 500ms
- Support 1000 concurrent conversations
- Maintain < $0.10 per video minute cost
- Achieve > 85% retrieval accuracy

Remember to check the old repository for implementation patterns and reuse code where appropriate!