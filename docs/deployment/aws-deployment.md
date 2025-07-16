# AWS ECS Deployment Guide

This guide walks you through deploying the Video Intelligence Platform on AWS ECS with GitHub Actions.

## Prerequisites

- AWS Account with appropriate permissions
- GitHub repository (forked or cloned)
- Docker images will be stored in Amazon ECR
- Services will run on AWS ECS Fargate

## Step 1: AWS Infrastructure Setup

### 1.1 Create IAM Roles

You need two IAM roles:

#### ECS Task Execution Role
This role allows ECS to pull images and write logs.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Attach these managed policies:
- `AmazonECSTaskExecutionRolePolicy`
- `AmazonSSMReadOnlyAccess` (for Secrets Manager)

#### ECS Task Role
This role gives your containers permissions to access AWS services.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-input-bucket/*",
        "arn:aws:s3:::your-output-bucket/*",
        "arn:aws:s3:::your-input-bucket",
        "arn:aws:s3:::your-output-bucket"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 1.2 Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name video-intelligence-backend \
  --region us-east-1
```

### 1.3 Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name video-intelligence-cluster \
  --region us-east-1
```

### 1.4 Create Application Load Balancer

1. Create an ALB for the API service
2. Configure target group for port 8003
3. Set up health check path: `/health`

### 1.5 Create CloudWatch Log Groups

```bash
aws logs create-log-group --log-group-name /ecs/video-intelligence-api
aws logs create-log-group --log-group-name /ecs/video-intelligence-worker
```

## Step 2: GitHub Actions Setup

### 2.1 Create GitHub OIDC Provider in AWS

This allows GitHub Actions to authenticate with AWS without storing credentials.

1. Go to IAM → Identity Providers
2. Add provider:
   - Provider Type: OpenID Connect
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`

### 2.2 Create IAM Role for GitHub Actions

Create a role with this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/video-intelligence-platform:*"
        }
      }
    }
  ]
}
```

Attach these policies:
- `AmazonEC2ContainerRegistryPowerUser`
- `AmazonECS_FullAccess`

### 2.3 Configure GitHub Secrets

In your GitHub repository settings, add these secrets:

```
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
AWS_GITHUB_ACTIONS_ROLE=arn:aws:iam::123456789012:role/GitHubActionsECSDeployRole
AWS_ECR_REPOSITORY=video-intelligence-backend
AWS_ECS_CLUSTER=video-intelligence-cluster
AWS_ECS_SERVICE_API=video-intelligence-api
AWS_ECS_SERVICE_WORKER=video-intelligence-worker
AWS_ECS_TASK_DEFINITION_API=video-intelligence-api
AWS_ECS_TASK_DEFINITION_WORKER=video-intelligence-worker
```

## Step 3: Secrets Management

### 3.1 Create Secrets in AWS Secrets Manager

Store sensitive values in Secrets Manager:

```bash
# MongoDB URL
aws secretsmanager create-secret \
  --name video-intelligence/mongodb-url \
  --secret-string "mongodb+srv://user:pass@cluster.mongodb.net/video-intelligence"

# Redis URL
aws secretsmanager create-secret \
  --name video-intelligence/redis-url \
  --secret-string "redis://your-redis-endpoint:6379"

# API Keys
aws secretsmanager create-secret \
  --name video-intelligence/openai-api-key \
  --secret-string "sk-..."

# S3 Buckets
aws secretsmanager create-secret \
  --name video-intelligence/s3-bucket \
  --secret-string "your-input-bucket"

# Add other secrets as needed...
```

### 3.2 Update Task Definition Templates

1. Copy the templates from `ecs/` directory
2. Replace placeholders:
   - `YOUR_ACCOUNT_ID`
   - `YOUR_REGION`
   - Update secret ARNs to match your created secrets

## Step 4: Create ECS Services

### 4.1 Register Task Definitions

```bash
# API Task Definition
aws ecs register-task-definition \
  --cli-input-json file://ecs/task-definition-api.json

# Worker Task Definition
aws ecs register-task-definition \
  --cli-input-json file://ecs/task-definition-worker.json
```

### 4.2 Create API Service

```bash
aws ecs create-service \
  --cluster video-intelligence-cluster \
  --service-name video-intelligence-api \
  --task-definition video-intelligence-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=video-intelligence-api,containerPort=8003"
```

### 4.3 Create Worker Service

```bash
aws ecs create-service \
  --cluster video-intelligence-cluster \
  --service-name video-intelligence-worker \
  --task-definition video-intelligence-worker:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Step 5: Deploy with GitHub Actions

Once everything is set up:

1. Push changes to the `main` branch
2. GitHub Actions will automatically:
   - Build the Docker image
   - Push to ECR
   - Update ECS services

Monitor the deployment in the Actions tab of your repository.

## Step 6: Verify Deployment

1. Check ECS console for running tasks
2. View CloudWatch logs for any errors
3. Test the API endpoint through the ALB

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names video-intelligence-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text

# Test health endpoint
curl http://your-alb-dns-name/health
```

## Cost Optimization

1. **Use Fargate Spot** for worker tasks (up to 70% savings)
2. **Set up auto-scaling** based on queue depth
3. **Use Reserved Capacity** for predictable workloads
4. **Enable S3 lifecycle policies** for processed videos

## Security Best Practices

1. **Use VPC endpoints** for S3 and ECR
2. **Enable VPC Flow Logs** for monitoring
3. **Implement least-privilege IAM policies**
4. **Enable AWS GuardDuty** for threat detection
5. **Use AWS WAF** on the ALB
6. **Enable encryption** at rest for all services

## Monitoring

1. **CloudWatch Dashboards**: Create dashboards for key metrics
2. **CloudWatch Alarms**: Set up alerts for errors, high latency
3. **X-Ray**: Enable distributed tracing
4. **Container Insights**: Monitor container performance

## Troubleshooting

### Common Issues

1. **Task fails to start**
   - Check CloudWatch logs
   - Verify IAM roles and permissions
   - Ensure secrets exist in Secrets Manager

2. **Cannot pull ECR image**
   - Verify ECR repository exists
   - Check task execution role permissions
   - Ensure VPC has internet access or VPC endpoints

3. **Service cannot connect to databases**
   - Verify security group rules
   - Check database endpoints in secrets
   - Ensure network connectivity

### Useful Commands

```bash
# View service logs
aws logs tail /ecs/video-intelligence-api --follow

# Check task status
aws ecs describe-tasks \
  --cluster video-intelligence-cluster \
  --tasks $(aws ecs list-tasks --cluster video-intelligence-cluster --service-name video-intelligence-api --query 'taskArns[0]' --output text)

# Force new deployment
aws ecs update-service \
  --cluster video-intelligence-cluster \
  --service video-intelligence-api \
  --force-new-deployment
```

## Next Steps

1. Set up monitoring and alerting
2. Configure auto-scaling policies
3. Implement backup strategies
4. Set up staging environment
5. Configure custom domain with Route 53