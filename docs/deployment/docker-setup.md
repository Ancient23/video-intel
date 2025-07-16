# Docker Setup Guide

This guide covers the Docker configuration for the Video Intelligence Platform.

## Overview

The platform uses Docker for both local development and production deployment. We use a single Dockerfile that can run both the API and Worker services with different commands.

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   MongoDB           │     │   Redis             │
│   (Document Store)  │     │   (Cache & Broker)  │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          ├────────────────────────────┤
          │                            │
┌─────────┴───────────┐     ┌─────────┴───────────┐
│   API Service       │     │   Worker Service    │
│   (FastAPI)         │     │   (Celery)          │
└─────────────────────┘     └─────────────────────┘
          │                            │
          └────────────┬───────────────┘
                       │
              ┌────────┴────────┐
              │   ChromaDB      │
              │   (Vector DB)   │
              └────────────────┘
```

## Local Development

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d mongodb redis

# View logs
docker-compose logs -f api worker

# Stop all services
docker-compose down

# Stop and remove volumes (full cleanup)
docker-compose down -v
```

### Service URLs

- **API**: http://localhost:8003
- **MongoDB**: mongodb://localhost:27017
- **Redis**: redis://localhost:6379
- **ChromaDB**: http://localhost:8000
- **Flower** (Celery monitor): http://localhost:5555

### Development Features

1. **Hot Reloading**: Code changes automatically reload the API
2. **Volume Mounts**: Local code is mounted into containers
3. **Debug Logging**: Detailed logs for development
4. **Local Databases**: MongoDB and Redis run in containers

## Docker Configuration Files

### Dockerfile

The Dockerfile is optimized for Python applications:

```dockerfile
FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY services/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/backend /app/services/backend

# Set Python path
ENV PYTHONPATH=/app/services/backend
ENV PYTHONUNBUFFERED=1

# Health check for API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Default command (API)
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### docker-compose.yml

The main compose file for local development includes:

- MongoDB with persistent storage
- Redis for caching and Celery
- ChromaDB for vector storage
- API service with hot reloading
- Worker service for background tasks
- Flower for Celery monitoring

### docker-compose.prod.yml

Production overrides that:
- Remove local databases (use managed services)
- Disable volume mounts
- Set production commands
- Configure resource limits
- Use environment variables from AWS

## Environment Variables

### Required Variables

```bash
# AWS (for S3 access)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=input-bucket
S3_OUTPUT_BUCKET=output-bucket

# Databases
MONGODB_URL=mongodb://mongodb:27017/video-intelligence
REDIS_URL=redis://redis:6379

# API Keys
OPENAI_API_KEY=sk-...
```

### Optional Variables

```bash
# NVIDIA API (for VILA)
NVIDIA_API_KEY=nvapi-...

# Vector DB
VECTOR_DB_TYPE=chromadb
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Performance
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_MEMORY_PER_CHILD=2048000
```

## Building Images

### Local Build

```bash
# Build the image
docker build -t video-intelligence-backend .

# Build with docker-compose
docker-compose build

# Build without cache
docker-compose build --no-cache
```

### Production Build

```bash
# Build and tag for ECR
docker build -t video-intelligence-backend .
docker tag video-intelligence-backend:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/video-intelligence-backend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/video-intelligence-backend:latest
```

## Health Checks

### API Health Check

The API exposes a `/health` endpoint:

```bash
curl http://localhost:8003/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "celery": "running"
  }
}
```

### Service Health Checks

Each service has built-in health checks:
- **MongoDB**: Connection ping
- **Redis**: PING command
- **ChromaDB**: Heartbeat endpoint
- **API**: HTTP health endpoint

## Resource Management

### Memory Limits

Services have configured memory limits:
- **API**: 2GB (dev) / 4GB (prod)
- **Worker**: 4GB (dev) / 8GB (prod)
- **MongoDB**: 2GB
- **Redis**: 1GB
- **ChromaDB**: 2GB

### CPU Limits

Production CPU limits:
- **API**: 2 CPUs
- **Worker**: 4 CPUs

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check container status
docker-compose ps

# Inspect container
docker inspect video-intelligence-api
```

### Permission Issues

```bash
# Fix permissions on volumes
sudo chown -R $USER:$USER ./data

# Remove volumes and restart
docker-compose down -v
docker-compose up -d
```

### Network Issues

```bash
# List networks
docker network ls

# Inspect network
docker network inspect video-intelligence-project_video-intelligence-network

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

### Database Connection Issues

```bash
# Test MongoDB connection
docker exec -it video-intelligence-mongodb mongosh

# Test Redis connection
docker exec -it video-intelligence-redis redis-cli ping
```

## Best Practices

1. **Use .dockerignore**: Exclude unnecessary files from build context
2. **Layer Caching**: Order Dockerfile commands for optimal caching
3. **Multi-stage Builds**: Use for smaller production images
4. **Health Checks**: Always include health check commands
5. **Resource Limits**: Set appropriate limits to prevent resource exhaustion
6. **Security**: Don't run containers as root in production
7. **Logging**: Use structured logging with proper log levels

## Advanced Usage

### Running Commands in Containers

```bash
# Run Python shell
docker-compose exec api python

# Run database migrations
docker-compose exec api python -m alembic upgrade head

# Run tests
docker-compose exec api pytest

# Access MongoDB shell
docker-compose exec mongodb mongosh
```

### Debugging

```bash
# Attach to running container
docker attach video-intelligence-api

# Execute commands
docker-compose exec api bash

# Copy files from container
docker cp video-intelligence-api:/app/logs/app.log ./
```

### Performance Monitoring

```bash
# View resource usage
docker stats

# View detailed container info
docker-compose top

# Monitor logs in real-time
docker-compose logs -f --tail=100
```

## Next Steps

1. [Local Development Guide](./local-development.md)
2. [Production Deployment](./aws-deployment.md)
3. [CI/CD Setup](./github-actions-setup.md)
4. [Monitoring Setup](./monitoring.md)