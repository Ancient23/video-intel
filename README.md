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
- Docker & Docker Compose
- 8GB+ RAM recommended

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd video-intelligence-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start services
docker compose up -d mongodb redis

# Initialize project
python scripts/init_project_status.py
python scripts/init_technical_debt.py

# Run tests
pytest services/backend/tests/
```

See [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md) for detailed setup instructions.

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

## Contributing

1. Check [Technical Debt](./docs/TECHNICAL_DEBT.md) for areas needing work
2. Follow patterns in the knowledge base
3. Update project status after changes
4. Add tests for new features
5. Document significant patterns

## License

[License information]
