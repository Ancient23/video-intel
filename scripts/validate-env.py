#!/usr/bin/env python3
"""
Environment validation script for Video Intelligence Platform.
Checks that all required environment variables are set and valid.
"""

import os
import sys
import re
from typing import Dict, List, Tuple, Optional

# Simple color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Create aliases for compatibility
class Fore:
    RED = Colors.RED
    GREEN = Colors.GREEN
    YELLOW = Colors.YELLOW
    BLUE = Colors.BLUE
    CYAN = Colors.CYAN
    GRAY = Colors.GRAY

class Style:
    BRIGHT = Colors.BOLD

# Define required and optional environment variables
REQUIRED_VARS = {
    # AWS Configuration
    "AWS_ACCESS_KEY_ID": {
        "description": "AWS access key for S3 and Rekognition",
        "pattern": r"^AKI[A-Z0-9]{16,}$",
        "example": "AKIAIOSFODNN7EXAMPLE"
    },
    "AWS_SECRET_ACCESS_KEY": {
        "description": "AWS secret key",
        "pattern": r"^.{40}$",
        "example": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    },
    "AWS_DEFAULT_REGION": {
        "description": "AWS region",
        "pattern": r"^[a-z]{2}-[a-z]+-\d{1}$",
        "example": "us-east-1"
    },
    "S3_BUCKET": {
        "description": "S3 bucket for input videos",
        "pattern": r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$",
        "example": "my-video-input-bucket"
    },
    "S3_OUTPUT_BUCKET": {
        "description": "S3 bucket for processed outputs",
        "pattern": r"^[a-z0-9][a-z0-9\-]{1,61}[a-z0-9]$",
        "example": "my-video-output-bucket"
    },
    
    # Database Configuration
    "MONGODB_URL": {
        "description": "MongoDB connection string",
        "pattern": r"^mongodb(\+srv)?://.*",
        "example": "mongodb://localhost:27017/video-intelligence"
    },
    "REDIS_URL": {
        "description": "Redis connection string",
        "pattern": r"^redis://.*",
        "example": "redis://localhost:6379"
    },
    
    # API Keys
    "OPENAI_API_KEY": {
        "description": "OpenAI API key for GPT models",
        "pattern": r"^sk-[a-zA-Z0-9]{48,}$",
        "example": "sk-...your-openai-key-here"
    }
}

OPTIONAL_VARS = {
    "NVIDIA_API_KEY": {
        "description": "NVIDIA API key for VILA analysis",
        "pattern": r"^nvapi-[a-zA-Z0-9\-_]{40,}$",
        "example": "nvapi-...your-nvidia-key-here"
    },
    "ANTHROPIC_API_KEY": {
        "description": "Anthropic API key for Claude models",
        "pattern": r"^sk-ant-[a-zA-Z0-9\-_]{40,}$",
        "example": "sk-ant-...your-anthropic-key-here"
    },
    "JWT_SECRET": {
        "description": "JWT secret for authentication",
        "pattern": r"^.{32,}$",
        "example": "your-secret-key-here-change-in-production"
    },
    "PINECONE_API_KEY": {
        "description": "Pinecone API key for vector database",
        "pattern": r"^[a-zA-Z0-9\-]{32,}$",
        "example": "your-pinecone-key-here"
    }
}


def check_env_var(var_name: str, var_config: Dict) -> Tuple[bool, Optional[str]]:
    """Check if an environment variable is set and valid."""
    value = os.environ.get(var_name)
    
    if not value:
        return False, "Not set"
    
    # Check pattern if provided
    pattern = var_config.get("pattern")
    if pattern and not re.match(pattern, value):
        return False, f"Invalid format (expected: {var_config['example']})"
    
    # Mask sensitive values for display
    if any(keyword in var_name for keyword in ["SECRET", "KEY", "PASSWORD"]):
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        return True, masked_value
    
    return True, value


def validate_aws_connection() -> bool:
    """Test AWS connection by checking S3 bucket access."""
    try:
        import boto3
        s3 = boto3.client('s3')
        
        # Try to list buckets to verify credentials
        s3.list_buckets()
        
        # Check if specified buckets exist
        input_bucket = os.environ.get('S3_BUCKET')
        output_bucket = os.environ.get('S3_OUTPUT_BUCKET')
        
        if input_bucket:
            try:
                s3.head_bucket(Bucket=input_bucket)
                print(f"{Fore.GREEN}✓ S3 input bucket accessible: {input_bucket}")
            except:
                print(f"{Fore.YELLOW}⚠ S3 input bucket not found or inaccessible: {input_bucket}")
                return False
                
        if output_bucket:
            try:
                s3.head_bucket(Bucket=output_bucket)
                print(f"{Fore.GREEN}✓ S3 output bucket accessible: {output_bucket}")
            except:
                print(f"{Fore.YELLOW}⚠ S3 output bucket not found or inaccessible: {output_bucket}")
                return False
                
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ AWS connection failed: {str(e)}")
        return False


def validate_database_urls() -> bool:
    """Validate database connection strings."""
    all_valid = True
    
    # Check MongoDB URL
    mongodb_url = os.environ.get('MONGODB_URL', '')
    if mongodb_url:
        if 'localhost' in mongodb_url or '127.0.0.1' in mongodb_url:
            print(f"{Fore.YELLOW}⚠ MongoDB URL points to localhost - ensure Docker is running")
        elif 'mongodb+srv://' in mongodb_url:
            print(f"{Fore.GREEN}✓ MongoDB Atlas URL detected")
        else:
            print(f"{Fore.GREEN}✓ MongoDB URL configured")
    
    # Check Redis URL
    redis_url = os.environ.get('REDIS_URL', '')
    if redis_url:
        if 'localhost' in redis_url or '127.0.0.1' in redis_url:
            print(f"{Fore.YELLOW}⚠ Redis URL points to localhost - ensure Docker is running")
        else:
            print(f"{Fore.GREEN}✓ Redis URL configured")
    
    return all_valid


def main():
    """Main validation function."""
    print(f"\n{Style.BRIGHT}Video Intelligence Platform - Environment Validation{Colors.END}")
    print("=" * 60)
    
    # Load .env file if it exists
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"\n{Fore.CYAN}Loading environment from {env_file}...{Colors.END}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            print(f"{Fore.YELLOW}Warning: python-dotenv not installed. Reading from system environment only.{Colors.END}")
    else:
        print(f"\n{Fore.YELLOW}No .env file found. Checking system environment variables...{Colors.END}")
    
    # Check required variables
    print(f"\n{Style.BRIGHT}Required Environment Variables:")
    print("-" * 60)
    
    missing_required = []
    invalid_required = []
    
    for var_name, var_config in REQUIRED_VARS.items():
        is_valid, value_or_error = check_env_var(var_name, var_config)
        
        if not is_valid:
            if value_or_error == "Not set":
                missing_required.append(var_name)
                print(f"{Fore.RED}✗ {var_name}: {value_or_error}")
            else:
                invalid_required.append((var_name, value_or_error))
                print(f"{Fore.RED}✗ {var_name}: {value_or_error}")
        else:
            print(f"{Fore.GREEN}✓ {var_name}: {value_or_error}")
        
        print(f"  {Fore.CYAN}{var_config['description']}")
    
    # Check optional variables
    print(f"\n{Style.BRIGHT}Optional Environment Variables:")
    print("-" * 60)
    
    for var_name, var_config in OPTIONAL_VARS.items():
        is_valid, value_or_error = check_env_var(var_name, var_config)
        
        if not is_valid and value_or_error != "Not set":
            print(f"{Fore.YELLOW}⚠ {var_name}: {value_or_error}")
        elif is_valid:
            print(f"{Fore.GREEN}✓ {var_name}: {value_or_error}")
        else:
            print(f"{Fore.GRAY}○ {var_name}: Not set")
        
        print(f"  {Fore.CYAN}{var_config['description']}")
    
    # Additional validations
    print(f"\n{Style.BRIGHT}Additional Validations:")
    print("-" * 60)
    
    # Test AWS connection if credentials are set
    if all(os.environ.get(var) for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']):
        validate_aws_connection()
    else:
        print(f"{Fore.YELLOW}⚠ Skipping AWS validation - credentials not set")
    
    # Validate database URLs
    validate_database_urls()
    
    # Summary
    print(f"\n{Style.BRIGHT}Summary:")
    print("=" * 60)
    
    if missing_required:
        print(f"{Fore.RED}Missing required variables: {', '.join(missing_required)}")
        print(f"\n{Fore.YELLOW}To fix:")
        print(f"1. Copy .env.example to .env")
        print(f"2. Fill in the missing values")
        print(f"3. Run this script again")
        return 1
    
    if invalid_required:
        print(f"{Fore.RED}Invalid required variables:")
        for var_name, error in invalid_required:
            print(f"  - {var_name}: {error}")
        return 1
    
    print(f"{Fore.GREEN}✅ All required environment variables are set and valid!")
    print(f"\n{Fore.CYAN}Next steps:")
    print(f"1. Run 'docker-compose up -d' to start services")
    print(f"2. Check service health with 'docker-compose ps'")
    print(f"3. Access the API at http://localhost:8003")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Validation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}")
        sys.exit(1)