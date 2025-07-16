# Video Intelligence Platform - Deployment Setup Guide

This guide will help you set up and deploy the Video Intelligence Platform in your own environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [AWS Deployment Setup](#aws-deployment-setup)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- Docker Desktop (latest version)
- Docker Compose v2.0+
- Python 3.11+
- Git
- AWS CLI v2 (for AWS deployment)

### Required Accounts

- AWS Account (for S3 storage and optional ECS deployment)
- OpenAI API account
- MongoDB Atlas account (for production) or local MongoDB
- Redis Cloud account (for production) or local Redis

### Optional Accounts

- NVIDIA API account (for VILA video analysis)
- Anthropic API account (for Claude models)
- Pinecone/Milvus account (for vector database)
- Sentry account (for error tracking)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/video-intelligence-platform.git
cd video-intelligence-platform
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual values
# IMPORTANT: Never commit .env with real credentials
```

### 3. Configure AWS Credentials

The platform uses AWS S3 for video storage. Configure your AWS credentials:

```bash
# Option 1: Using AWS CLI
aws configure

# Option 2: Set environment variables in .env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1
```

### 4. Create S3 Buckets

Create two S3 buckets in your AWS account:
- Input bucket: for source videos
- Output bucket: for processed results

Update `.env` with your bucket names:
```
S3_BUCKET=your-input-bucket
S3_OUTPUT_BUCKET=your-output-bucket
```

### 5. Start Services with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 6. Verify Services

Check that all services are running:

```bash
# Check service status
docker-compose ps

# Test API health
curl http://localhost:8003/health

# Access services:
# - API: http://localhost:8003
# - MongoDB: localhost:27017
# - Redis: localhost:6379
# - ChromaDB: http://localhost:8000
# - Flower (Celery monitoring): http://localhost:5555
```

## AWS Deployment Setup

For production deployment on AWS ECS, follow the [AWS Deployment Guide](./aws-deployment.md).

## Configuration

### Environment Variables

See `.env.example` for all available configuration options. Key variables:

- **AWS Configuration**: S3 access and bucket names
- **Database URLs**: MongoDB and Redis connections
- **API Keys**: OpenAI, NVIDIA, etc.
- **Feature Flags**: Enable/disable specific features
- **Security**: JWT secrets, CORS settings

### Docker Configuration

- `docker-compose.yml`: Local development with hot reloading
- `docker-compose.prod.yml`: Production overrides
- `Dockerfile`: Multi-stage build for API and Worker

### Service Configuration

Each service can be configured via environment variables:

- **API**: Port, workers, logging level
- **Worker**: Concurrency, memory limits, task routing
- **MongoDB**: Connection string, database name
- **Redis**: Connection string, database number
- **Vector DB**: Type (ChromaDB/Milvus/Pinecone), connection details

## Troubleshooting

### Common Issues

1. **Services won't start**
   - Check Docker is running
   - Verify port availability (8003, 27017, 6379, 8000, 5555)
   - Check logs: `docker-compose logs [service-name]`

2. **Cannot connect to AWS S3**
   - Verify AWS credentials in `.env`
   - Check bucket names and regions
   - Ensure IAM permissions for S3 access

3. **MongoDB connection issues**
   - Ensure MongoDB container is healthy
   - Check connection string format
   - Verify network connectivity between services

4. **Worker not processing tasks**
   - Check Redis connection
   - Verify Celery broker URL
   - Check worker logs for errors

### Getting Help

- Check the [documentation](../README.md)
- Search [GitHub Issues](https://github.com/your-org/video-intelligence-platform/issues)
- Join our [Discord community](https://discord.gg/your-invite)

## Next Steps

1. [Configure AWS Deployment](./aws-deployment.md)
2. [Set up CI/CD](./github-actions-setup.md)
3. [Production Best Practices](./production-guide.md)
4. [API Documentation](../api/README.md)