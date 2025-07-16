#!/bin/bash
# Run tests locally using development Docker services

set -e

echo "🧪 Running tests locally with Docker services..."

# Parse command line arguments
TEST_PATH=${1:-""}
EXTRA_ARGS=${@:2}

# Ensure services are running
echo "🚀 Starting development services..."
docker compose up -d mongodb redis chromadb

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 5

# Export test environment variables
export MONGODB_URL="mongodb://localhost:27017/video-intelligence-test"
export REDIS_URL="redis://localhost:6379/1"
export ENVIRONMENT="test"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export S3_BUCKET="test-bucket"
export S3_OUTPUT_BUCKET="test-output-bucket"
export OPENAI_API_KEY="test"
export NVIDIA_API_KEY="test"

# Create test results directory
mkdir -p test-results

# Change to backend directory
cd services/backend

# Run tests
if [ -z "$TEST_PATH" ]; then
    echo "🧪 Running all tests..."
    python -m pytest tests/ \
        --cov=. \
        --cov-report=html:../../test-results/htmlcov \
        --cov-report=term \
        --junit-xml=../../test-results/junit.xml \
        -v \
        $EXTRA_ARGS
else
    echo "🧪 Running tests: $TEST_PATH"
    python -m pytest "$TEST_PATH" \
        --cov=. \
        --cov-report=html:../../test-results/htmlcov \
        --cov-report=term \
        -v \
        $EXTRA_ARGS
fi

echo "✅ Tests completed! Coverage report available in test-results/htmlcov/"