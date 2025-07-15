# Production Deployment Preparation

## Description
Prepare components or the full application for deployment to AWS infrastructure.

## When to Use
- Preparing for first production deployment
- Setting up new environments (staging, prod)
- Deploying new services or components
- Updating deployment configurations
- Preparing for scaling events

## Prerequisites
- AWS account with appropriate permissions
- Docker images building successfully
- Environment variables documented
- Secrets management strategy defined
- Cost estimates calculated

## Deployment Architecture

### Target Infrastructure
- **Compute**: AWS ECS Fargate
- **Database**: MongoDB Atlas / AWS DocumentDB
- **Cache**: AWS ElastiCache (Redis)
- **Storage**: AWS S3
- **Secrets**: AWS Secrets Manager
- **Monitoring**: CloudWatch + DataDog/New Relic

## Pre-Deployment Checklist

### 1. Code Readiness

```bash
# All tests passing
pytest services/backend/tests/

# No critical technical debt
./dev-cli prompt debt-check | grep CRITICAL

# Code quality checks
black services/backend/ --check
mypy services/backend/
pylint services/backend/

# Security scan
bandit -r services/backend/
```

### 2. Configuration Audit

```bash
# Check deployment patterns from VideoCommentator
./dev-cli ask "AWS deployment checklist"
./dev-cli ask "ECS configuration patterns"

# List all environment variables
grep -h "os.getenv\|os.environ" -r services/backend/ | sort | uniq

# Verify all have defaults or are documented
cat .env.example
```

### 3. Docker Preparation

#### Dockerfile Optimization
```dockerfile
# Multi-stage build for smaller images
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Security: Run as non-root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy only necessary files
COPY --from=builder /root/.local /home/appuser/.local
COPY services/backend/ ./services/backend/

# Set Python path
ENV PYTHONPATH=/app
ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "services.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Test
```bash
# Build image
docker build -t video-intelligence:latest .

# Test locally
docker run -p 8000:8000 \
  --env-file .env \
  video-intelligence:latest

# Check image size
docker images video-intelligence:latest

# Security scan
docker scan video-intelligence:latest
```

## AWS Infrastructure Setup

### 1. ECS Task Definition

```json
{
  "family": "video-intelligence-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/VideoIntelligenceTaskRole",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/VideoIntelligenceExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/video-intelligence:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APP_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "MONGODB_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:video-intelligence/mongodb"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:video-intelligence/openai"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/video-intelligence",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### 2. Celery Worker Task Definition

```json
{
  "family": "video-intelligence-worker",
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "worker",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/video-intelligence:latest",
      "command": ["celery", "-A", "services.backend.celery_app", "worker", "--loglevel=info"],
      "environment": [
        {
          "name": "WORKER_MAX_MEMORY_PER_CHILD",
          "value": "3072000"
        },
        {
          "name": "WORKER_MAX_TASKS_PER_CHILD",
          "value": "100"
        }
      ]
    }
  ]
}
```

### 3. Resource Requirements

Based on VideoCommentator lessons:

| Service | CPU | Memory | Count | Notes |
|---------|-----|---------|-------|-------|
| API | 1 vCPU | 2 GB | 2-10 | Auto-scale on CPU |
| Worker | 2 vCPU | 4 GB | 1-20 | Auto-scale on queue |
| Beat | 0.5 vCPU | 1 GB | 1 | Single instance |

### 4. Auto-Scaling Configuration

```yaml
API Service:
  Target CPU: 70%
  Min Tasks: 2
  Max Tasks: 10
  Scale Up: +2 tasks when CPU > 70% for 2 min
  Scale Down: -1 task when CPU < 30% for 10 min

Worker Service:
  Target Metric: Queue Length
  Min Tasks: 1
  Max Tasks: 20
  Scale Up: +4 tasks when queue > 100
  Scale Down: -2 tasks when queue < 10
```

## Secrets Management

### 1. Create Secrets in AWS

```bash
# MongoDB connection
aws secretsmanager create-secret \
  --name video-intelligence/mongodb \
  --secret-string "mongodb+srv://user:pass@cluster.mongodb.net/video_intelligence"

# API Keys
aws secretsmanager create-secret \
  --name video-intelligence/openai \
  --secret-string "sk-..."

# AWS credentials (if not using IAM roles)
aws secretsmanager create-secret \
  --name video-intelligence/aws \
  --secret-string '{"access_key":"...","secret_key":"..."}'
```

### 2. IAM Permissions

Task role policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::video-intelligence-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:*:*:secret:video-intelligence/*"
      ]
    }
  ]
}
```

## Monitoring Setup

### 1. CloudWatch Alarms

```bash
# High CPU usage
aws cloudwatch put-metric-alarm \
  --alarm-name video-intelligence-high-cpu \
  --alarm-description "API CPU above 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# High error rate
aws cloudwatch put-metric-alarm \
  --alarm-name video-intelligence-errors \
  --alarm-description "Error rate above 1%" \
  --metric-name 5XXError \
  --threshold 1
```

### 2. Application Metrics

Add to application:
```python
# services/backend/utils/metrics.py
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def send_metric(metric_name: str, value: float, unit='Count'):
    """Send custom metric to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='VideoIntelligence',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
        ]
    )

# Usage
send_metric('VideoProcessed', 1)
send_metric('ProcessingTime', 45.3, 'Seconds')
```

## Database Preparation

### 1. MongoDB Atlas Setup

- Create M10+ cluster for production
- Enable backup with point-in-time recovery
- Configure VPC peering with AWS
- Set up monitoring alerts
- Create read-only user for analytics

### 2. Connection String

```python
# Production connection with all options
MONGODB_URL = "mongodb+srv://user:pass@cluster.mongodb.net/video_intelligence?retryWrites=true&w=majority&maxPoolSize=50&minPoolSize=10"
```

## Cost Optimization

### 1. ECS Fargate Spot

For workers (can handle interruptions):
```json
{
  "capacityProviderStrategy": [
    {
      "capacityProvider": "FARGATE_SPOT",
      "weight": 4
    },
    {
      "capacityProvider": "FARGATE",
      "weight": 1
    }
  ]
}
```

### 2. S3 Lifecycle Policies

```bash
# Move processed videos to cheaper storage
aws s3api put-bucket-lifecycle-configuration \
  --bucket video-intelligence-output \
  --lifecycle-configuration file://lifecycle.json

# lifecycle.json
{
  "Rules": [
    {
      "Id": "ArchiveOldVideos",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

## Deployment Process

### 1. Build and Push Image

```bash
# Build
docker build -t video-intelligence:$(git rev-parse --short HEAD) .

# Tag
docker tag video-intelligence:$(git rev-parse --short HEAD) \
  ACCOUNT.dkr.ecr.REGION.amazonaws.com/video-intelligence:latest

# Login to ECR
aws ecr get-login-password --region REGION | \
  docker login --username AWS --password-stdin \
  ACCOUNT.dkr.ecr.REGION.amazonaws.com

# Push
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/video-intelligence:latest
```

### 2. Update ECS Service

```bash
# Update service with new image
aws ecs update-service \
  --cluster video-intelligence \
  --service api \
  --force-new-deployment

# Monitor deployment
aws ecs describe-services \
  --cluster video-intelligence \
  --services api \
  --query 'services[0].deployments'
```

### 3. Health Checks

```bash
# Check service health
curl https://api.video-intelligence.com/health

# Check metrics
aws cloudwatch get-metric-statistics \
  --namespace VideoIntelligence \
  --metric-name VideoProcessed \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Rollback Plan

### 1. Quick Rollback

```bash
# Revert to previous task definition
aws ecs update-service \
  --cluster video-intelligence \
  --service api \
  --task-definition video-intelligence-api:PREVIOUS_REVISION
```

### 2. Database Rollback

- MongoDB point-in-time recovery
- Keep migration rollback scripts ready
- Test rollback procedure regularly

## Post-Deployment

### 1. Monitoring Checklist
- [ ] All health checks passing
- [ ] Error rates normal
- [ ] Response times acceptable
- [ ] CPU/Memory usage stable
- [ ] No unusual log entries

### 2. Performance Validation
- [ ] Load test key endpoints
- [ ] Verify auto-scaling works
- [ ] Check cache hit rates
- [ ] Monitor database performance

### 3. Documentation Updates
- [ ] Update runbooks
- [ ] Document new endpoints
- [ ] Update architecture diagrams
- [ ] Share deployment notes

## Production Readiness Checklist

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Secrets in AWS Secrets Manager
- [ ] IAM roles configured
- [ ] Monitoring alerts set up
- [ ] Auto-scaling configured
- [ ] Backup strategy implemented
- [ ] Rollback plan tested
- [ ] Documentation updated
- [ ] Team trained on procedures

## Related Prompts
- `local-setup` - Local environment setup
- `arch-decision` - Architecture decisions
- `test` - Testing strategies
- `doc-sync` - Documentation updates