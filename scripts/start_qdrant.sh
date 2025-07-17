#!/bin/bash

echo "🚀 Starting Qdrant Vector Database"
echo ""
echo "Please ensure Docker Desktop is running first!"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    echo ""
    echo "On macOS: Open Docker Desktop from Applications"
    exit 1
fi

# Create storage directory
mkdir -p qdrant_storage

# Stop existing container if running
docker stop qdrant 2>/dev/null
docker rm qdrant 2>/dev/null

# Start Qdrant
echo "Starting Qdrant container..."
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:6333/health > /dev/null; then
        echo "✅ Qdrant is ready!"
        echo ""
        echo "Qdrant Dashboard: http://localhost:6333/dashboard"
        echo "API Endpoint: http://localhost:6333"
        exit 0
    fi
    sleep 1
done

echo "❌ Qdrant failed to start within 30 seconds"
exit 1