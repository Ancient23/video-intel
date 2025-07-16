#!/bin/bash
# Run tests in watch mode for development

set -e

echo "👁️  Running tests in watch mode..."

# Use the test profile from docker-compose.yml
docker compose run --rm \
    --service-ports \
    test \
    python -m pytest tests/ \
    --tb=short \
    -v \
    --maxfail=1 \
    --color=yes \
    -x \
    ${@}

echo "✅ Test watch mode ended"