# Graph-RAG Setup Guide

## Overview

The Video Intelligence Platform now supports Graph-RAG (Graph-enhanced Retrieval Augmented Generation), combining:
- **Qdrant**: Vector database for semantic similarity search
- **Neo4j**: Graph database for relationship-based knowledge retrieval
- **MongoDB**: Document storage for knowledge persistence

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   MongoDB   │────▶│ Population   │────▶│   Qdrant    │
│ (Documents) │     │   Script     │     │  (Vectors)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                      ┌─────────────┐
                      │    Neo4j    │
                      │   (Graph)   │
                      └─────────────┘
```

## Quick Start

### 1. Start Services

```bash
# Start all services including Neo4j
docker compose up -d

# Verify services are running
docker compose ps
```

Services and ports:
- MongoDB: `localhost:27017`
- Redis: `localhost:6379`
- Qdrant: `http://localhost:6333`
- Neo4j: `http://localhost:7474` (Browser), `bolt://localhost:7687` (Bolt)
- API: `http://localhost:8003`

### 2. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Add to your `.env` file:
```env
# Vector Database
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=video_intelligence_kb

# Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

### 4. Test Setup

```bash
# Run test script to verify all connections
python scripts/test_graph_rag.py
```

### 5. Populate Knowledge Base

```bash
# Run the unified population script
python scripts/populate_knowledge_graph.py
```

This will:
- Process PDF research documents
- Clone and analyze GitHub repositories
- Extract entities and relationships
- Build both vector and graph indices

## Using Graph-RAG

### CLI Commands

```bash
# Basic knowledge base info
./dev-cli info

# Search with Graph-RAG (default)
./dev-cli search "how to implement video chunking"

# Search without graph enhancement
./dev-cli search "RAG patterns" --no-graph

# Explore entity relationships
./dev-cli explore "Qdrant" --depth 3

# Traditional commands still work
./dev-cli ask "What are the best practices for video processing?"
./dev-cli suggest "video analysis provider"
```

### Programmatic Usage

```python
from dev_knowledge_base.rag.graph_rag_assistant import GraphRAGAssistant

# Initialize
assistant = GraphRAGAssistant()

# Search with graph enhancement
results = assistant.search("video processing patterns", use_graph=True)

# Ask questions
answer = assistant.ask("How should I implement the chunking service?", use_graph=True)

# Explore relationships
graph = assistant.explore_relationships("MongoDB", max_depth=2)
```

## Knowledge Sources

### Currently Configured Sources

1. **PDF Documents** (`dev-knowledge-base/docs/pdfs/`)
   - NVIDIA Blueprint documentation
   - Architecture guides

2. **GitHub Repositories**
   - NVIDIA-AI-Blueprints (video-search, rag, etc.)
   - mlfoundations/open_clip
   - haotian-liu/LLaVA
   - qdrant/qdrant
   - neo4j/neo4j

3. **Internal Documentation**
   - Product Requirements Document
   - README files
   - CLAUDE.md

4. **Online Resources**
   - Graph-RAG implementation guides

### Adding New Sources

Edit `scripts/populate_knowledge_graph.py` to add new sources:

```python
# Add new GitHub repo
repos = [
    # ... existing repos ...
    ("https://github.com/your/repo", ["README.md", "src/**/*.py"]),
]

# Add new PDF
pdf_files = list(pdf_dir.glob("*.pdf"))  # Automatically picks up new PDFs
```

## Neo4j Graph Structure

### Node Types
- `KnowledgeNode`: Document chunks with embeddings
- `Entity`: Extracted entities (technologies, concepts, etc.)

### Relationship Types
- `MENTIONS`: KnowledgeNode mentions an Entity
- `SIMILAR_TO`: Similarity between KnowledgeNodes
- Custom relationships based on content

### Example Queries

Access Neo4j browser at `http://localhost:7474` (user: neo4j, password: password123)

```cypher
// Find all knowledge about Qdrant
MATCH (n:KnowledgeNode)-[:MENTIONS]->(e:Entity {name: "Qdrant"})
RETURN n.title, n.category

// Find related technologies
MATCH (e1:Entity {name: "RAG"})-[*1..2]-(e2:Entity)
WHERE e1 <> e2
RETURN DISTINCT e2.name, e2.type

// Find similar documents
MATCH (n1:KnowledgeNode {category: "video_processing"})-[r:SIMILAR_TO]->(n2)
WHERE r.score > 0.8
RETURN n1.title, n2.title, r.score
```

## Troubleshooting

### Qdrant Issues
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# View Qdrant dashboard
open http://localhost:6333/dashboard
```

### Neo4j Issues
```bash
# Check Neo4j logs
docker compose logs neo4j

# Reset Neo4j password if needed
docker compose exec neo4j cypher-shell -u neo4j -p neo4j \
  "ALTER USER neo4j SET PASSWORD 'password123'"
```

### Python 3.13 SSL Issues
```bash
# If you get SSL certificate errors
export SSL_CERT_FILE=$(python -m certifi)
export REQUESTS_CA_BUNDLE=$(python -m certifi)
```

## Performance Tips

1. **Batch Operations**: The population script processes in batches for efficiency
2. **Lazy Loading**: Components only initialize when needed
3. **Caching**: Qdrant and Neo4j cache frequently accessed data
4. **Async Operations**: MongoDB operations are async for better performance

## Next Steps

1. **Enhance Entity Extraction**: Enable SpaCy for better NLP
   ```bash
   pip install spacy
   python -m spacy download en_core_web_sm
   ```

2. **Add More Sources**: Include more GitHub repos and documentation
3. **Custom Extractors**: Create domain-specific entity extractors
4. **Graph Analytics**: Use Neo4j Graph Data Science library