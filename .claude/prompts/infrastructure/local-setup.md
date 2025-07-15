# Local Development Setup

## Description
Set up a local development environment for working on specific components or the full Video Intelligence Platform.

## When to Use
- Starting development on a new machine
- Setting up after cloning the repository  
- Troubleshooting environment issues
- Onboarding new developers
- Creating isolated test environments

## Prerequisites
- Git installed
- Python 3.11+ installed
- Docker Desktop installed
- 8GB+ RAM available
- Basic command line knowledge

## Setup Steps

### 1. Environment Check

Verify prerequisites:
```bash
# Check Python version
python --version  # Should be 3.11+

# Check Docker
docker --version
docker compose version

# Check available memory
# macOS
sysctl hw.memsize

# Linux
free -h

# Verify ports are available
lsof -i :27017  # MongoDB
lsof -i :6379   # Redis
lsof -i :8000   # FastAPI
```

### 2. Clone and Initialize

```bash
# Clone repository
git clone [repository-url]
cd video-intelligence-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Environment Configuration

Create `.env` file:
```bash
# Copy example
cp .env.example .env

# Edit with your values
cat > .env << 'EOF'
# MongoDB
MONGODB_URL=mongodb://localhost:27017/video_intelligence

# Redis
REDIS_URL=redis://localhost:6379

# AWS (for development, use LocalStack or test credentials)
AWS_ACCESS_KEY_ID=test_key
AWS_SECRET_ACCESS_KEY=test_secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=test-input-bucket
S3_OUTPUT_BUCKET=test-output-bucket

# API Keys (get from team or use test keys)
OPENAI_API_KEY=your_openai_key
NVIDIA_API_KEY=your_nvidia_key  # Optional

# Application
APP_ENV=development
LOG_LEVEL=DEBUG

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
EOF
```

### 4. Start Infrastructure

```bash
# Start MongoDB and Redis
docker compose up -d mongodb redis

# Verify services are running
docker compose ps

# Check logs if needed
docker compose logs mongodb
docker compose logs redis

# Wait for services to be ready
sleep 5
```

### 5. Initialize Database

```bash
# Initialize project status
python scripts/init_project_status.py

# Initialize technical debt tracking
python scripts/init_technical_debt.py

# Verify MongoDB connection
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
print('MongoDB databases:', client.list_database_names())
"
```

### 6. Knowledge Base Setup

```bash
# Test knowledge base
./dev-cli ask "Setup complete?"

# If issues, rebuild knowledge base
cd dev-knowledge-base
python ingestion/extract_knowledge.py
cd ..
```

### 7. Run Tests

Verify setup:
```bash
# Run basic tests
pytest services/backend/tests/test_models/ -v

# Run specific test
pytest services/backend/tests/test_models/test_video.py::test_video_creation -v

# Check test coverage
pytest --cov=services.backend --cov-report=term-missing
```

### 8. Start Development Server

```bash
# Start FastAPI development server
cd services/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A celery_app worker --loglevel=info

# In another terminal, start Celery beat (if using scheduled tasks)
celery -A celery_app beat --loglevel=info
```

### 9. Verify Everything Works

```bash
# Check API health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs

# Test a simple endpoint
curl -X GET http://localhost:8000/api/v1/videos

# Check Celery workers
celery -A celery_app inspect active
```

## Component-Specific Setup

### For Video Processing Only
```bash
# Install FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Verify
ffmpeg -version
```

### For Knowledge Graph Development
```bash
# Additional dependencies
pip install neo4j networkx

# Start Neo4j (optional, if using)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### For Embedding Development
```bash
# Install additional ML dependencies
pip install sentence-transformers torch

# For GPU support (optional)
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker compose ps mongodb

# Check MongoDB logs
docker compose logs --tail=50 mongodb

# Try connecting directly
docker compose exec mongodb mongosh

# Restart if needed
docker compose restart mongodb
```

### Redis Connection Issues
```bash
# Check Redis
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping

# Clear Redis if needed (WARNING: deletes all data)
docker compose exec redis redis-cli FLUSHALL
```

### Python Dependencies Issues
```bash
# Clear pip cache
pip cache purge

# Reinstall in correct order
pip install -r requirements.txt --force-reinstall

# If specific package fails
pip install [package-name] --no-cache-dir
```

### Port Conflicts
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 [PID]

# Or use different port
uvicorn main:app --port 8001
```

### Knowledge Base Issues
```bash
# Rebuild ChromaDB
cd dev-knowledge-base
rm -rf .chroma/
python ingestion/extract_knowledge.py

# Test query
./dev-cli ask "test query"
```

## Development Tools Setup

### VS Code Configuration
Create `.vscode/settings.json`:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "services/backend/tests"
    ],
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Quick Start Commands

After initial setup, use these for daily development:

```bash
# Start everything
./scripts/start-dev.sh

# Or manually:
docker compose up -d mongodb redis
source venv/bin/activate
cd services/backend
uvicorn main:app --reload
```

## Cleanup

To completely clean the environment:

```bash
# Stop all services
docker compose down -v

# Remove virtual environment
deactivate
rm -rf venv/

# Remove local data
rm -rf .chroma/
rm -f .env

# Remove Docker volumes (WARNING: deletes all data)
docker volume prune
```

## Next Steps

1. Run status check:
   ```bash
   ./dev-cli prompt status-check
   ```

2. Check for any setup issues:
   ```bash
   ./dev-cli prompt debt-check
   ```

3. Start developing:
   ```bash
   ./dev-cli prompt next-task
   ```

## Related Prompts
- `deploy-prep` - Production deployment setup
- `bug` - Troubleshooting issues
- `test` - Testing setup
- `knowledge-query` - Query patterns