# Video Intelligence Platform - Product Requirements Document (PRD)

## Executive Summary

This document outlines a complete architectural redesign of the VideoCommentator platform to transform it into a comprehensive Video Intelligence Platform with advanced knowledge memory capabilities. The platform will leverage RAG/Graph-RAG technologies and MongoDB for persistent video timeline storage, enabling intelligent conversational AI about video content.

## Vision

Create a scalable, plugin-based video analysis platform that:
1. **Pre-processes** videos to build comprehensive knowledge graphs and embeddings
2. **Stores** structured intelligence in MongoDB with rich metadata and relationships
3. **Enables** real-time conversational AI during video playback using pre-computed artifacts
4. **Supports** any AI model/provider through a flexible plugin architecture
5. **Optimizes** for AWS deployment with cost-effective processing

## Core Architecture Principles

Based on the NVIDIA Blueprint architecture, we'll implement a two-phase system:
1. **Ingestion Phase**: Heavy processing to extract all possible information
2. **Runtime Phase**: Lightweight retrieval and generation for real-time chat

The system will use:
- **Vector Database** for semantic search over video content
- **Knowledge Graph** for structured entity relationships and temporal events

## Detailed Technical Architecture

### Phase 1: Video Ingestion & Knowledge Building

#### 1.1 Video Chunking Service
```python
# services/backend/services/chunking/
├── video_chunker.py          # Intelligent video segmentation
├── shot_detector.py          # Shot boundary detection
├── scene_analyzer.py         # Scene-level grouping
└── keyframe_extractor.py     # Representative frame selection
```

**Implementation Details:**
- Start with AWS Rekognition shot detection for baseline segmentation
- Extract keyframes at shot boundaries and significant visual changes
- Support configurable chunk sizes (5-30 seconds) based on content type
- Cache raw chunks in S3 with standardized naming: `{video_id}/chunks/chunk_{index}.mp4`

#### 1.2 Multi-Modal Analysis Pipeline
```python
# services/backend/services/analysis/
├── base_analyzer.py          # Abstract base class for all analyzers
├── providers/
│   ├── aws_rekognition.py   # AWS Rekognition integration
│   ├── nvidia_vila.py        # NVIDIA VILA/Cosmos VLM
│   ├── openai_vision.py     # GPT-4 Vision
│   ├── google_video_ai.py   # Google Video Intelligence
│   └── custom_vlm.py         # Template for custom models
├── audio_analyzer.py         # Speech transcription & analysis
└── orchestrator.py           # Parallel execution coordinator
```

**Key Features:**
- Each chunk gets dense captions from VLMs and structured metadata from object detection
- Object tracking across frames with persistent IDs for characters/objects
- Audio transcription with speaker diarization
- Parallel processing with provider-specific optimizations

#### 1.3 Knowledge Graph Construction
```python
# services/backend/services/knowledge_graph/
├── graph_builder.py          # Core graph construction
├── entity_extractor.py       # NER and entity linking
├── relationship_mapper.py    # Relationship extraction
├── temporal_indexer.py       # Time-based event indexing
└── mongodb_adapter.py        # MongoDB graph storage
```

Following NVIDIA's approach:
- Nodes represent entities (characters, objects, locations)
- Edges represent relationships and interactions with timestamps
- Events captured as special nodes with temporal ordering

**MongoDB Schema:**
```javascript
// Scenes Collection
{
  _id: ObjectId,
  video_id: string,
  scene_number: number,
  start_time: float,
  end_time: float,
  shots: [
    {
      shot_id: string,
      start_time: float,
      end_time: float,
      keyframe_url: string,
      dense_caption: string,
      visual_embeddings: float[],
      detected_objects: [{
        object_id: string,
        label: string,
        confidence: float,
        bounding_box: object
      }],
      provider_metadata: object
    }
  ],
  summary: string,
  themes: string[],
  mood: string,
  graph_nodes: [ObjectId]  // References to graph nodes
}

// Knowledge Graph Collection
{
  _id: ObjectId,
  video_id: string,
  node_type: "entity" | "event" | "relationship",
  label: string,
  properties: object,
  embeddings: float[],
  temporal_range: {
    start: float,
    end: float
  },
  connections: [{
    target_node: ObjectId,
    relationship_type: string,
    properties: object
  }]
}
```

#### 1.4 Embedding & Indexing Service
```python
# services/backend/services/embeddings/
├── embedding_generator.py    # Multi-modal embeddings
├── vector_store.py          # Vector database interface
├── index_manager.py         # Index optimization
└── providers/
    ├── milvus_store.py      # Milvus integration
    ├── pinecone_store.py    # Pinecone alternative
    └── faiss_store.py       # Local FAISS option
```

Embeddings enable semantic search over video content, allowing queries like "What was the protagonist doing in the first scene?"

### Phase 2: Runtime Chatbot Orchestration

#### 2.1 Context-Aware RAG System
```python
# services/backend/services/rag/
├── retriever.py             # Multi-source retrieval
├── context_builder.py       # Dynamic context assembly
├── graph_rag.py            # Graph-enhanced retrieval
└── reranker.py             # Result reranking
```

Implement NVIDIA's Context-Aware RAG approach:
- Retrieve relevant chunks based on current timestamp and query
- Use knowledge graph for fact-checking and relationship queries
- Maintain conversation context across the film duration

#### 2.2 Conversational Engine
```python
# services/backend/services/conversation/
├── chat_manager.py          # Conversation state management
├── response_generator.py    # LLM response generation
├── tts_service.py          # Text-to-speech generation
├── streaming_handler.py     # WebSocket/SSE streaming
└── persona_manager.py       # Chatbot personality system
```

**Features:**
- Real-time response generation synchronized with video playback
- Multiple chatbot personas with different expertise/perspectives
- TTS with emotion and timing for natural conversation
- Support for multiple simultaneous conversations

#### 2.3 MCP Server Implementation
```python
# services/backend/mcp/
├── server.py               # MCP server implementation
├── video_tools.py          # Video-specific MCP tools
├── conversation_tools.py   # Conversation management tools
└── client_examples/        # Example client implementations
```

Following Anthropic's Model Context Protocol for:
- Standardized tool interfaces
- Context window management
- Multi-agent coordination

## API Design

### Core Endpoints

**Pre-processing Phase:**
```yaml
# Video Upload & Processing
POST /api/v1/videos/upload
POST /api/v1/videos/{video_id}/process
GET  /api/v1/videos/{video_id}/status

# Analysis Management
POST /api/v1/analysis/start
GET  /api/v1/analysis/{job_id}/status
GET  /api/v1/analysis/{job_id}/artifacts

# Knowledge Graph
GET  /api/v1/knowledge/{video_id}/graph
POST /api/v1/knowledge/{video_id}/query
```

**Runtime Phase:**
```yaml
# Conversation Management
POST /api/v1/conversations/create
GET  /api/v1/conversations/{conv_id}
POST /api/v1/conversations/{conv_id}/message
GET  /api/v1/conversations/{conv_id}/context

# Real-time Streaming
WS   /api/v1/conversations/{conv_id}/stream
GET  /api/v1/conversations/{conv_id}/tts/{message_id}

# MCP Interface
POST /mcp/v1/tools/list
POST /mcp/v1/tools/execute
```

## Technology Stack

### Backend Infrastructure
- **Framework**: FastAPI with async support
- **Task Queue**: Celery with Redis broker
- **Message Queue**: Redis Streams for real-time events
- **Caching**: Redis with intelligent TTLs

### Storage & Databases
- **Primary Storage**: MongoDB Atlas (managed)
- **Vector Database**: Milvus (self-hosted) or Pinecone (managed)
- **Object Storage**: AWS S3 with CloudFront CDN
- **Graph Database**: MongoDB with graph queries or Neo4j

### AI/ML Services
- **Orchestration**: LangChain/LangGraph for complex workflows
- **Embeddings**: OpenAI Ada-3 or custom CLIP models
- **LLMs**: Provider-agnostic with support for:
  - OpenAI GPT-4
  - Anthropic Claude
  - NVIDIA Llama models via NIM
  - Custom fine-tuned models

### Deployment (AWS Optimized)
- **Compute**: ECS Fargate for API/Workers
- **GPU Processing**: EC2 with GPU for local model inference
- **Load Balancing**: ALB with WebSocket support
- **Auto-scaling**: Based on queue depth and CPU/memory

## Implementation Phases

### Phase 1: Foundation (Weeks 1-3)
1. Set up MongoDB schema and connections
2. Implement video chunking pipeline
3. Create provider plugin architecture
4. Basic ingestion workflow with AWS Rekognition

### Phase 2: Knowledge Building (Weeks 4-6)
1. Implement knowledge graph construction
2. Add embedding generation and vector storage
3. Create timeline merging logic
4. Build artifact storage system

### Phase 3: RAG Implementation (Weeks 7-9)
1. Implement retrieval system
2. Create context-aware response generation
3. Add conversation management
4. Basic API endpoints

### Phase 4: Real-time Features (Weeks 10-12)
1. WebSocket implementation
2. TTS integration with timing
3. Multi-conversation support
4. Performance optimization

### Phase 5: Production Readiness (Weeks 13-15)
1. Comprehensive testing
2. Monitoring and observability
3. Documentation
4. Deployment automation

## Reusable Components from Existing Codebase

### Keep and Enhance:
1. **Provider Abstraction** (`services/backend/services/video_analysis/`)
   - Extend base class for new providers
   - Add capability discovery system

2. **S3 Utilities** (`services/backend/services/s3_utils.py`)
   - Add intelligent caching layer
   - Implement CDN integration

3. **Redis Caching** (`services/backend/utils/cache_utils.py`)
   - Extend for graph caching
   - Add embedding cache

4. **Task Structure** (`services/backend/tasks/`)
   - Refactor into domain-specific modules
   - Add Celery Canvas workflows

5. **FFmpeg Integration** (`services/backend/utils/mux.py`)
   - Keep for final video generation
   - Add streaming support

### Replace:
1. **Timeline Generation** - Move to graph-based approach
2. **Script Generation** - Integrate with RAG system
3. **Orchestration** - Use Celery Canvas instead of monolithic task

### New Additions:
1. **MongoDB Integration** - For persistent storage
2. **Vector Database** - For semantic search
3. **Knowledge Graph Engine** - For relationship queries
4. **MCP Server** - For standardized tool access
5. **WebSocket Support** - For real-time communication

## Cost Optimization Strategies

Following best practices:
1. **Preprocessing**: Use batch processing and spot instances
2. **Caching**: Aggressive caching at every layer
3. **Model Selection**: Use smaller models where appropriate
4. **Storage**: Lifecycle policies for S3 artifacts

## Security Considerations

1. **API Authentication**: JWT tokens with refresh mechanism
2. **Data Encryption**: At-rest and in-transit
3. **Access Control**: Role-based permissions
4. **Audit Logging**: Comprehensive activity tracking
5. **PII Handling**: Automatic detection and masking

## Success Metrics

### Performance
- Video processing: < 2x real-time
- Query response: < 500ms p95
- TTS generation: < 200ms per sentence

### Quality
- Knowledge graph completeness: > 90% entity coverage
- Retrieval accuracy: > 85% relevant results
- User satisfaction: > 4.5/5 rating

### Scale
- Support 1000+ concurrent conversations
- Process 10TB+ video per month
- < $0.10 per minute of video processed

## Next Steps

### Immediate Actions
1. Set up MongoDB Atlas cluster
2. Create provider plugin template
3. Implement basic chunking service
4. Design API contracts

### Technical Decisions
1. Choose vector database (Milvus vs Pinecone)
2. Select primary LLM provider
3. Decide on graph query language

### Team Requirements
1. Backend engineers familiar with FastAPI/Celery
2. ML engineers for model integration
3. DevOps for AWS infrastructure
4. Frontend engineers for client applications

## Appendix: Reference Architecture

This architecture is based on:
- NVIDIA's Multi-Modal AI Pipeline Blueprint
- VideoCommentator's proven patterns
- Industry best practices for RAG systems
- Scalable microservices design principles

The platform provides a solid foundation for building a scalable video intelligence system that can grow from MVP to enterprise-scale deployment while maintaining flexibility and performance.