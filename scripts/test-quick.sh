#!/bin/bash
# Quick test runner for development - runs tests using existing services

set -e

echo "🧪 Running quick tests..."

# Change to backend directory
cd services/backend

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

# Run specific test or all tests
if [ -z "$1" ]; then
    echo "Running all tests..."
    python -m pytest tests/ -v --tb=short
else
    echo "Running tests matching: $1"
    python -m pytest tests/ -k "$1" -v --tb=short
fi