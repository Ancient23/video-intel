#!/bin/bash
# Run tests inside Docker containers with isolated test databases

set -e

echo "🧪 Running tests in Docker environment..."

# Parse command line arguments
TEST_PATH=${1:-""}
EXTRA_ARGS=${@:2}

# Create test results directory
mkdir -p test-results

# Build the Docker image if needed
echo "📦 Building Docker image..."
docker compose build api

# Run tests with docker-compose.test.yml (isolated databases)
if [ -z "$TEST_PATH" ]; then
    echo "🚀 Running all tests with isolated test databases..."
    docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
else
    echo "🚀 Running tests: $TEST_PATH"
    docker compose -f docker-compose.test.yml run --rm test-runner \
        python -m pytest "$TEST_PATH" \
        --cov=. \
        --cov-report=html:/test-results/htmlcov \
        --cov-report=term \
        -v \
        $EXTRA_ARGS
fi

# Clean up
echo "🧹 Cleaning up test containers..."
docker compose -f docker-compose.test.yml down -v

echo "✅ Tests completed! Coverage report available in test-results/htmlcov/"