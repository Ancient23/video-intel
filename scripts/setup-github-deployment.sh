#!/bin/bash

# Video Intelligence Platform - GitHub Deployment Setup Script
# This script helps you configure GitHub secrets for AWS deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Video Intelligence Platform - GitHub Deployment Setup${NC}"
echo "======================================================"
echo ""
echo "This script will help you configure GitHub secrets for AWS deployment."
echo "You'll need:"
echo "  - GitHub CLI (gh) installed and authenticated"
echo "  - AWS account with appropriate permissions"
echo "  - Your GitHub repository URL"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI is not authenticated.${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Get repository information
echo -e "${YELLOW}Step 1: Repository Information${NC}"
echo "Enter your GitHub repository (e.g., owner/repo):"
read -r GITHUB_REPO

# Verify repository exists
if ! gh repo view "$GITHUB_REPO" &> /dev/null; then
    echo -e "${RED}Error: Repository $GITHUB_REPO not found or not accessible.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Repository verified${NC}"
echo ""

# Collect AWS information
echo -e "${YELLOW}Step 2: AWS Configuration${NC}"
echo "Enter your AWS region (e.g., us-east-1):"
read -r AWS_REGION

echo "Enter your AWS account ID (12 digits):"
read -r AWS_ACCOUNT_ID

echo "Enter your ECR repository name (e.g., video-intelligence-backend):"
read -r AWS_ECR_REPOSITORY

echo "Enter your ECS cluster name (e.g., video-intelligence-cluster):"
read -r AWS_ECS_CLUSTER

echo "Enter your API service name (e.g., video-intelligence-api):"
read -r AWS_ECS_SERVICE_API

echo "Enter your Worker service name (e.g., video-intelligence-worker):"
read -r AWS_ECS_SERVICE_WORKER

echo "Enter your API task definition family (e.g., video-intelligence-api):"
read -r AWS_ECS_TASK_DEFINITION_API

echo "Enter your Worker task definition family (e.g., video-intelligence-worker):"
read -r AWS_ECS_TASK_DEFINITION_WORKER

echo "Enter your GitHub Actions IAM role ARN:"
echo "(e.g., arn:aws:iam::123456789012:role/GitHubActionsECSDeployRole)"
read -r AWS_GITHUB_ACTIONS_ROLE

echo ""
echo -e "${YELLOW}Step 3: Creating GitHub Secrets${NC}"
echo "The following secrets will be created in your repository:"
echo ""

# Display summary
echo "AWS_REGION=$AWS_REGION"
echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID"
echo "AWS_ECR_REPOSITORY=$AWS_ECR_REPOSITORY"
echo "AWS_ECS_CLUSTER=$AWS_ECS_CLUSTER"
echo "AWS_ECS_SERVICE_API=$AWS_ECS_SERVICE_API"
echo "AWS_ECS_SERVICE_WORKER=$AWS_ECS_SERVICE_WORKER"
echo "AWS_ECS_TASK_DEFINITION_API=$AWS_ECS_TASK_DEFINITION_API"
echo "AWS_ECS_TASK_DEFINITION_WORKER=$AWS_ECS_TASK_DEFINITION_WORKER"
echo "AWS_GITHUB_ACTIONS_ROLE=$AWS_GITHUB_ACTIONS_ROLE"
echo ""

echo "Continue? (y/n)"
read -r CONFIRM

if [[ $CONFIRM != "y" ]]; then
    echo "Cancelled."
    exit 0
fi

# Create secrets
echo ""
echo "Creating secrets..."

gh secret set AWS_REGION -b "$AWS_REGION" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_REGION${NC}"

gh secret set AWS_ACCOUNT_ID -b "$AWS_ACCOUNT_ID" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ACCOUNT_ID${NC}"

gh secret set AWS_ECR_REPOSITORY -b "$AWS_ECR_REPOSITORY" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ECR_REPOSITORY${NC}"

gh secret set AWS_ECS_CLUSTER -b "$AWS_ECS_CLUSTER" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ECS_CLUSTER${NC}"

gh secret set AWS_ECS_SERVICE_API -b "$AWS_ECS_SERVICE_API" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ECS_SERVICE_API${NC}"

gh secret set AWS_ECS_SERVICE_WORKER -b "$AWS_ECS_SERVICE_WORKER" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ECS_SERVICE_WORKER${NC}"

gh secret set AWS_ECS_TASK_DEFINITION_API -b "$AWS_ECS_TASK_DEFINITION_API" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ECS_TASK_DEFINITION_API${NC}"

gh secret set AWS_ECS_TASK_DEFINITION_WORKER -b "$AWS_ECS_TASK_DEFINITION_WORKER" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_ECS_TASK_DEFINITION_WORKER${NC}"

gh secret set AWS_GITHUB_ACTIONS_ROLE -b "$AWS_GITHUB_ACTIONS_ROLE" -R "$GITHUB_REPO"
echo -e "${GREEN}✓ AWS_GITHUB_ACTIONS_ROLE${NC}"

echo ""
echo -e "${GREEN}Success! All GitHub secrets have been configured.${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Ensure your AWS infrastructure is set up (see docs/deployment/aws-deployment.md)"
echo "2. Create your ECS task definitions using the templates in ecs/"
echo "3. Push changes to the main branch to trigger deployment"
echo "4. Monitor the deployment in the GitHub Actions tab"
echo ""
echo -e "${BLUE}Additional Resources:${NC}"
echo "- AWS Setup Guide: docs/deployment/aws-deployment.md"
echo "- Docker Setup: docs/deployment/docker-setup.md"
echo "- Troubleshooting: docs/deployment/troubleshooting.md"