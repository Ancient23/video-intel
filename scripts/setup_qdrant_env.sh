#!/bin/bash

echo "🚀 Setting up Qdrant Knowledge Base Environment"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Current Python version: $PYTHON_VERSION"

# Create virtual environment with Python 3.11 if available
if command -v python3.11 &> /dev/null; then
    echo "✅ Found Python 3.11, creating virtual environment..."
    python3.11 -m venv venv-qdrant
    VENV_CREATED=true
elif command -v python3.12 &> /dev/null; then
    echo "✅ Found Python 3.12, creating virtual environment..."
    python3.12 -m venv venv-qdrant
    VENV_CREATED=true
else
    echo "⚠️  Python 3.11 or 3.12 not found. Using default Python 3..."
    echo "Note: You may experience compatibility issues with Python 3.13"
    python3 -m venv venv-qdrant
    VENV_CREATED=true
fi

if [ "$VENV_CREATED" = true ]; then
    echo ""
    echo "✅ Virtual environment created: venv-qdrant"
    echo ""
    echo "📝 Next steps:"
    echo "1. Activate the environment:"
    echo "   source venv-qdrant/bin/activate"
    echo ""
    echo "2. Install dependencies:"
    echo "   pip install -r dev-knowledge-base-requirements.txt"
    echo ""
    echo "3. Make sure Qdrant is running:"
    echo "   docker ps | grep qdrant"
    echo ""
    echo "4. Run population scripts:"
    echo "   python scripts/populate_modern_knowledge_base_qdrant.py"
    echo ""
    echo "5. Test with dev-cli:"
    echo "   ./dev-cli status"
    echo "   ./dev-cli ask 'What is the Video Intelligence Platform?'"
else
    echo "❌ Failed to create virtual environment"
    exit 1
fi