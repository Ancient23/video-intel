# Video Intelligence Platform

A scalable video analysis platform that transforms videos into searchable, conversational knowledge bases.

## Architecture

- **Pre-processing Phase**: Extract comprehensive knowledge from videos
- **Runtime Phase**: Enable real-time conversational AI during video playback

## Quick Links

- 📊 [Project Management Guide](./docs/PROJECT_MANAGEMENT.md) - Track progress and tasks
- 🐛 [Technical Debt Tracking](./docs/TECHNICAL_DEBT.md) - Known issues and TODOs
- 🚀 [Developer Onboarding](./docs/DEVELOPER_ONBOARDING.md) - Getting started guide
- 📋 [Product Requirements](./docs/new/video-intelligence-prd.md) - Detailed specifications
- 🔧 [Scripts Documentation](./scripts/README.md) - Management script usage

## Project Status

Check current project status and technical debt:

```bash
# View project progress
source venv/bin/activate
python scripts/init_project_status.py

# View technical debt
python scripts/init_technical_debt.py

# Quick status summary
./dev-cli status
```

### Current Phase: FOUNDATION
- ✅ MongoDB setup complete
- ✅ Video chunking implemented
- ✅ Provider architecture ready
- 🚧 API endpoints in progress
- 📝 16 open technical debt items

## Development Knowledge Base

This project includes a development knowledge base powered by the same RAG technology we're building.

### Knowledge Base Commands

```bash
# Query development patterns
./dev-cli ask "How should I implement video chunking?"

# Get implementation suggestions
./dev-cli suggest "mongodb_models"

# Find solutions to problems
./dev-cli ask "How to handle large video files?"
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose v2.0+
- AWS Account (for S3 storage)
- 8GB+ RAM recommended

### 🚀 30-Second Setup

```bash
# Clone and enter the repository
git clone https://github.com/your-org/video-intelligence-platform.git
cd video-intelligence-platform

# Copy environment template and configure
cp .env.example .env
# Edit .env with your AWS credentials and API keys

# Validate your environment
python scripts/validate-env.py

# Start all services with Docker
docker-compose up -d

# Verify everything is running
docker-compose ps
curl http://localhost:8003/health
```

### Service URLs
- 🌐 **API**: http://localhost:8003
- 📊 **Flower** (Celery monitor): http://localhost:5555
- 🗄️ **MongoDB**: localhost:27017
- 🔄 **Redis**: localhost:6379
- 🧠 **ChromaDB**: http://localhost:8000

### Detailed Setup

```bash
# 1. Environment Configuration
cp .env.example .env
# Configure these required variables:
# - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# - S3_BUCKET, S3_OUTPUT_BUCKET (must exist in your AWS account)
# - OPENAI_API_KEY

# 2. Validate Configuration
python scripts/validate-env.py

# 3. Start Services
docker-compose up -d

# 4. Check Service Health
docker-compose ps
docker-compose logs -f  # View logs

# 5. Optional: Set up Python environment for development
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r services/backend/requirements.txt

# 6. Run Tests
docker-compose exec api pytest
```

### 🚢 Production Deployment

Deploy to AWS ECS with GitHub Actions:

```bash
# Set up GitHub secrets for deployment
./scripts/setup-github-deployment.sh

# Push to main branch to trigger deployment
git push origin main
```

See [AWS Deployment Guide](./docs/deployment/aws-deployment.md) for complete instructions.

## Development Workflow

1. **Check Status**: Review project and debt status
2. **Pick Task**: Choose from current tasks or high-priority debt
3. **Query Patterns**: Use knowledge base for implementation guidance
4. **Implement**: Follow established patterns
5. **Update Status**: Track progress and any new debt
6. **Test**: Ensure quality with comprehensive tests

See [Project Management Guide](./docs/PROJECT_MANAGEMENT.md) for detailed workflows.

## Key Features

- 🎥 **Multi-Provider Video Analysis**: AWS Rekognition, NVIDIA VILA, OpenAI
- 🧠 **Knowledge Graph Construction**: Entity and relationship extraction
- 🔍 **Semantic Search**: Vector embeddings with RAG
- 💬 **Conversational AI**: Real-time video Q&A
- 📊 **Cost Optimization**: Smart caching and provider selection
- 🔄 **Scalable Architecture**: Celery-based distributed processing

## Project Structure

```
video-intelligence-project/
├── services/
│   └── backend/
│       ├── api/              # FastAPI endpoints
│       ├── workers/          # Celery tasks
│       ├── services/         # Business logic
│       ├── models/           # MongoDB schemas
│       └── tests/           # Test suite
├── docs/                    # Documentation
├── scripts/                 # Management scripts
├── dev-knowledge-base/      # Development RAG system
└── PROMPTS.md              # AI assistant templates
```

## Docker Support

The platform includes complete Docker support for both development and production:

### Development
- **Hot Reloading**: Code changes automatically reload
- **All Services**: MongoDB, Redis, ChromaDB, API, Worker, Flower
- **Volume Mounts**: Your code is synced with containers
- **Easy Commands**: `docker-compose up -d` to start everything

### Production
- **Optimized Images**: Multi-stage builds with FFmpeg
- **AWS ECS Ready**: Task definitions and GitHub Actions included
- **Secrets Management**: AWS Secrets Manager integration
- **Auto-scaling**: Based on load and queue depth

See [Docker Setup Guide](./docs/deployment/docker-setup.md) for details.

## Contributing

1. Check [Technical Debt](./docs/TECHNICAL_DEBT.md) for areas needing work
2. Follow patterns in the knowledge base
3. Update project status after changes
4. Add tests for new features
5. Document significant patterns

## License

[License information]
