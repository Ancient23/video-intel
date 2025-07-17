# Qdrant Migration Guide

## Overview
We've migrated from ChromaDB to Qdrant for the development knowledge base due to:
- Python 3.13 compatibility issues with ChromaDB
- Better performance and scalability
- Production-ready features for AWS deployment

## Quick Start

### 1. Start Qdrant
```bash
# Using the provided script (checks Docker is running)
./scripts/start_qdrant.sh

# Or manually
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

### 2. Set Up Python Environment
Due to Python 3.13 compatibility issues, we recommend using Python 3.11 or 3.12:

```bash
# Run the setup script
./scripts/setup_qdrant_env.sh

# Activate the new environment
source venv-qdrant/bin/activate

# Install dependencies
pip install -r dev-knowledge-base-requirements.txt
```

### 3. Populate Knowledge Base
```bash
# Run the Qdrant-compatible population scripts
python scripts/populate_modern_knowledge_base_qdrant.py
# Additional population scripts coming soon...
```

### 4. Test the System
```bash
./dev-cli status
./dev-cli ask "What is the Video Intelligence Platform?"
```

## Configuration

The following environment variables have been added to `.env`:

```env
# Vector Database Configuration
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Optional for local development
QDRANT_COLLECTION_NAME=video_intelligence_kb
```

## Architecture Changes

### Before (ChromaDB)
- Local persistent storage in `./knowledge/chromadb`
- Python 3.13 compatibility issues
- Limited to development use

### After (Qdrant)
- Docker-based vector database
- Better performance and scalability
- Same API can be used for production on AWS
- GraphRAG ready (can integrate with Neo4j)

## Files Changed

1. **New Files**:
   - `dev-knowledge-base/rag/dev_assistant_qdrant.py` - Qdrant-compatible RAG
   - `scripts/populate_modern_knowledge_base_qdrant.py` - Qdrant population script
   - `scripts/start_qdrant.sh` - Docker startup helper
   - `scripts/setup_qdrant_env.sh` - Python environment setup
   - `dev-knowledge-base-requirements.txt` - Updated dependencies

2. **Modified Files**:
   - `.env` - Added Qdrant configuration
   - `dev-knowledge-base/rag/dev_assistant.py` - Replaced with Qdrant version

3. **Backup Files**:
   - `dev-knowledge-base/rag/dev_assistant_chromadb_backup.py` - Original ChromaDB version

## Troubleshooting

### Python SSL Errors
If you see SSL certificate errors, use the setup script to create a fresh environment:
```bash
./scripts/setup_qdrant_env.sh
```

### Docker Not Running
```bash
# On macOS
open /Applications/Docker.app

# Then verify
docker ps
```

### Qdrant Connection Issues
```bash
# Check if Qdrant is running
curl http://localhost:6333

# Check logs
docker logs qdrant
```

## Production Deployment

The same Qdrant setup can be deployed to AWS:

1. **AWS ECS**: Deploy Qdrant container to ECS/Fargate
2. **Qdrant Cloud**: Use managed Qdrant service
3. **Configuration**: Update `QDRANT_URL` in production `.env`

## Next Steps

1. Complete migration of all population scripts
2. Add GraphRAG capabilities with Neo4j integration
3. Implement production deployment scripts
4. Create performance benchmarks

## Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [LangChain Qdrant Integration](https://python.langchain.com/docs/integrations/vectorstores/qdrant)
- [GraphRAG with Qdrant and Neo4j](https://qdrant.tech/documentation/examples/graphrag-qdrant-neo4j/)