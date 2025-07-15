#!/bin/bash
# setup-dev-knowledge-base.sh
# Quick setup script for the development knowledge base

set -e

echo "🚀 Setting up Video Intelligence Platform Development Knowledge Base"

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required but not installed."
        exit 1
    fi
    
    # Check if old repo path is provided
    if [ -z "$1" ]; then
        echo "❌ Usage: ./setup-dev-knowledge-base.sh <path_to_old_repo> [path_to_pdfs]"
        exit 1
    fi
    
    OLD_REPO_PATH="$1"
    PDF_PATH="${2:-./pdfs}"
    
    if [ ! -d "$OLD_REPO_PATH" ]; then
        echo "❌ Old repository path does not exist: $OLD_REPO_PATH"
        exit 1
    fi
    
    echo "✅ Prerequisites checked"
}

# Create project structure
create_structure() {
    echo "📁 Creating project structure..."
    
    # Main directories
    mkdir -p video-intelligence-platform/{services,infrastructure,docker,scripts,docs}
    mkdir -p video-intelligence-platform/services/{backend,mcp}
    mkdir -p video-intelligence-platform/services/backend/{api,workers,core,services,models,schemas,tests}
    
    # Knowledge base directories
    mkdir -p video-intelligence-platform/dev-knowledge-base/{ingestion,knowledge,mongodb,rag,docs,tools}
    mkdir -p video-intelligence-platform/dev-knowledge-base/knowledge/{embeddings,graphs,summaries}
    mkdir -p video-intelligence-platform/dev-knowledge-base/docs/{imported,pdfs,new}
    
    echo "✅ Project structure created"
}

# Setup Python environment
setup_python() {
    echo "🐍 Setting up Python environment..."
    
    cd video-intelligence-platform
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Create requirements files
    cat > requirements-dev.txt << 'EOF'
# Development Knowledge Base Requirements
langchain==0.1.0
langchain-openai==0.0.5
chromadb==0.4.22
beanie==1.25.0
motor==3.3.2
pymongo==4.6.1
click==8.1.7
rich==13.7.0
PyPDF2==3.0.1
python-frontmatter==1.0.1
httpx==0.26.0
pydantic==2.5.3
structlog==24.1.0
python-dotenv==1.0.1
EOF

    cat > requirements.txt << 'EOF'
# Main Application Requirements
fastapi==0.104.1
celery==5.3.4
redis==5.0.1
motor==3.3.2
pymongo==4.6.1
langchain==0.1.0
langchain-openai==0.0.5
pydantic==2.5.3
httpx==0.26.0
boto3==1.34.34
structlog==24.1.0
python-multipart==0.0.6
websockets==12.0
uvicorn==0.27.0
python-dotenv==1.0.1
EOF

    # Install requirements
    pip install -r requirements-dev.txt
    
    echo "✅ Python environment ready"
}

# Setup MongoDB
setup_mongodb() {
    echo "🍃 Setting up MongoDB..."
    
    # Start MongoDB container
    docker run -d \
        --name video-intel-devdb \
        -p 27017:27017 \
        -v video-intel-mongodb:/data/db \
        mongo:7
    
    # Wait for MongoDB to be ready
    echo "Waiting for MongoDB to start..."
    sleep 5
    
    echo "✅ MongoDB running on port 27017"
}

# Copy and setup knowledge extraction scripts
setup_scripts() {
    echo "📝 Setting up knowledge extraction scripts..."
    
    # Copy the CLAUDE_INSTRUCTIONS.md
    cp "$OLD_REPO_PATH/CLAUDE_INSTRUCTIONS.md" ./CLAUDE_INSTRUCTIONS.md 2>/dev/null || \
    echo "# Video Intelligence Platform - Claude CLI Instructions" > ./CLAUDE_INSTRUCTIONS.md
    
    # Update the OLD_REPO_PATH in instructions
    sed -i.bak "s|\[OLD_REPO_PATH\]|$OLD_REPO_PATH|g" ./CLAUDE_INSTRUCTIONS.md
    rm -f ./CLAUDE_INSTRUCTIONS.md.bak
    
    # Create the main knowledge population script
    cat > ./scripts/populate_knowledge_base.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_knowledge_base.ingestion.inventory_old_docs import DocumentInventory
from dev_knowledge_base.ingestion.extract_knowledge import KnowledgeExtractor
from dev_knowledge_base.ingestion.pdf_extractor import PDFKnowledgeExtractor

async def main(old_repo_path: str, pdf_dir: str):
    print(f"📚 Populating knowledge base from: {old_repo_path}")
    print(f"📄 PDFs directory: {pdf_dir}")
    
    # Implementation will be added by Claude CLI
    print("✅ Knowledge base population complete!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: populate_knowledge_base.py <old_repo_path> <pdf_dir>")
        sys.exit(1)
    
    asyncio.run(main(sys.argv[1], sys.argv[2]))
EOF

    chmod +x ./scripts/populate_knowledge_base.py
    
    echo "✅ Scripts created"
}

# Create initial documentation
create_docs() {
    echo "📚 Creating initial documentation..."
    
    cat > ./README.md << 'EOF'
# Video Intelligence Platform

A scalable video analysis platform that transforms videos into searchable, conversational knowledge bases.

## Architecture

- **Pre-processing Phase**: Extract comprehensive knowledge from videos
- **Runtime Phase**: Enable real-time conversational AI during video playback

## Development Knowledge Base

This project includes a development knowledge base powered by the same RAG technology we're building.

### Quick Start

```bash
# Query development patterns
./dev-cli ask "How should I implement video chunking?"

# Get implementation suggestions
./dev-cli suggest "mongodb_models"

# Check project status
./dev-cli status
```

## Setup

See `DEVELOPMENT_SETUP.md` for detailed setup instructions.
EOF

    cat > ./DEVELOPMENT_SETUP.md << EOF
# Development Setup

## Prerequisites

- Python 3.11+
- Docker
- MongoDB (via Docker)
- Redis (via Docker)

## Knowledge Base Setup

The development knowledge base has been initialized with:
- Documentation from: $OLD_REPO_PATH
- PDF blueprints from: $PDF_PATH

To query the knowledge base:
\`\`\`bash
source venv/bin/activate
./dev-cli ask "your question here"
\`\`\`

## Next Steps

1. Run Claude CLI to implement the knowledge extraction scripts
2. Populate the knowledge base
3. Start implementing core services

See \`CLAUDE_INSTRUCTIONS.md\` for detailed implementation guidance.
EOF

    echo "✅ Documentation created"
}

# Create .env template
create_env_template() {
    echo "🔐 Creating environment template..."
    
    cat > .env.example << 'EOF'
# Application
APP_NAME=video-intelligence-platform
ENVIRONMENT=development

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=video_intelligence

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1
S3_BUCKET=video-intelligence-dev
S3_OUTPUT_BUCKET=video-intelligence-output

# AI Providers
OPENAI_API_KEY=your_openai_key
NVIDIA_API_KEY=your_nvidia_key
ANTHROPIC_API_KEY=your_anthropic_key

# Vector Database
VECTOR_DB_TYPE=chromadb
MILVUS_HOST=localhost:19530
PINECONE_API_KEY=your_pinecone_key
EOF

    # Copy existing .env if available
    if [ -f "$OLD_REPO_PATH/.env" ]; then
        echo "📋 Copying API keys from old .env file..."
        cp "$OLD_REPO_PATH/.env" .env
        echo "⚠️  Please update .env with any new required variables"
    else
        cp .env.example .env
        echo "⚠️  Please update .env with your API keys"
    fi
    
    echo "✅ Environment template created"
}

# Create development CLI tool
create_dev_cli() {
    echo "🛠️  Creating development CLI..."
    
    cat > ./dev-cli << 'EOF'
#!/usr/bin/env python3
import click
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dev_knowledge_base.tools.dev_cli import cli

if __name__ == "__main__":
    cli()
EOF

    chmod +x ./dev-cli
    
    echo "✅ Development CLI created"
}

# Main execution
main() {
    check_prerequisites "$@"
    
    echo "🏗️  Setting up Video Intelligence Platform..."
    
    create_structure
    setup_python
    setup_mongodb
    setup_scripts
    create_docs
    create_env_template
    create_dev_cli
    
    # Copy PDFs if provided
    if [ -d "$PDF_PATH" ]; then
        echo "📄 Copying PDF documents..."
        cp -r "$PDF_PATH"/* ./video-intelligence-platform/dev-knowledge-base/docs/pdfs/ 2>/dev/null || true
    fi
    
    # Import critical docs from old repo
    echo "📚 Importing critical documentation..."
    mkdir -p ./video-intelligence-platform/dev-knowledge-base/docs/imported
    
    # Copy specific directories
    for dir in "current" "reference" "guides" "history" "planning"; do
        if [ -d "$OLD_REPO_PATH/apps/web/docs/$dir" ]; then
            cp -r "$OLD_REPO_PATH/apps/web/docs/$dir" \
                ./video-intelligence-platform/dev-knowledge-base/docs/imported/
        fi
    done
    
    cd video-intelligence-platform
    
    echo ""
    echo "✨ Setup complete!"
    echo ""
    echo "📍 Project created at: $(pwd)"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. cd video-intelligence-platform"
    echo "   2. source venv/bin/activate"
    echo "   3. Update .env with your API keys"
    echo "   4. Run: claude 'Following CLAUDE_INSTRUCTIONS.md, implement the knowledge extraction scripts'"
    echo "   5. Run: python scripts/populate_knowledge_base.py '$OLD_REPO_PATH' ./dev-knowledge-base/docs/pdfs"
    echo "   6. Start developing with: ./dev-cli ask 'your question'"
    echo ""
    echo "📖 See DEVELOPMENT_SETUP.md for more details"
}

# Run main with all arguments
main "$@"