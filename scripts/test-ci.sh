#!/bin/bash
# Run tests in CI/CD environment (GitHub Actions)

set -e

echo "🧪 Running tests in CI environment..."

# Create test results directory
mkdir -p test-results

# Run tests with docker-compose.test.yml
docker compose -f docker-compose.test.yml build
docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner

# Copy test results
docker compose -f docker-compose.test.yml cp test-runner:/test-results/. ./test-results/

# Clean up
docker compose -f docker-compose.test.yml down -v

echo "✅ Tests completed!"