"""S3 utilities for downloading/uploading files."""

import os
import tempfile
import boto3
import json
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger()

def get_s3_client():
    """Get S3 client configured for AWS S3."""
    # Let boto3 use its credential chain (env vars, IAM role, etc.)
    # Only explicitly set credentials if they exist in environment
    kwargs = {
        'service_name': 's3',
        'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    }
    
    # Only add explicit credentials if they exist
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        kwargs['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
        kwargs['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    return boto3.client(**kwargs)

def is_s3_uri(uri: str) -> bool:
    """Returns True if uri is an S3 URI (s3://bucket/key)."""
    if not uri:
        return False
    try:
        parsed = urlparse(uri)
        return parsed.scheme == 's3'
    except:
        return False

def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an S3 URI into (bucket, key) tuple."""
    parsed = urlparse(uri)
    if parsed.scheme != 's3':
        raise ValueError(f"Not an S3 URI: {uri}")
    return parsed.netloc, parsed.path.lstrip('/')

def check_s3_object_exists(bucket: str, key: str) -> bool:
    """
    Check if an object exists in S3.
    
    Args:
        bucket: The S3 bucket name
        key: The object key in the bucket
        
    Returns:
        bool: True if the object exists, False otherwise
    """
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        # If a 404 error is returned, the object does not exist
        if e.response['Error']['Code'] == '404':
            return False
        # For other errors, we raise the exception
        raise

def download_from_s3(uri: str, target_path: str = None) -> str:
    """
    Download a file from S3 to a local path.
    If target_path is None, downloads to a temporary file.
    Returns the local file path.
    """
    bucket, key = parse_s3_uri(uri)
    
    if target_path is None:
        # Create temp file with same extension as source
        _, ext = os.path.splitext(key)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        target_path = temp.name
        temp.close()

    s3 = get_s3_client()
    s3.download_file(bucket, key, target_path)
    return target_path

def upload_to_s3(local_file_path: str, bucket: str, key: str = None) -> str:
    """
    Upload a local file to an S3 bucket.
    If key is not provided, uses the filename from local_file_path.
    Returns the S3 URI of the uploaded file.
    """
    if key is None:
        key = os.path.basename(local_file_path)
    
    s3 = get_s3_client()
    s3.upload_file(local_file_path, bucket, key)
    return f"s3://{bucket}/{key}"

def upload_content_to_s3(content: bytes | str, bucket: str, key: str, content_type: Optional[str] = None) -> str:
    """
    Upload in-memory content (bytes or string) to an S3 object.
    If content is str, it's encoded to UTF-8.
    Returns the S3 URI of the uploaded object.
    """
    s3 = get_s3_client()
    body_content = content.encode('utf-8') if isinstance(content, str) else content
    
    extra_args = {}
    if content_type:
        extra_args['ContentType'] = content_type
        
    s3.put_object(Bucket=bucket, Key=key, Body=body_content, **extra_args)
    return f"s3://{bucket}/{key}"

def upload_files_to_s3(local_file_paths: List[str], bucket: str, prefix: str = "") -> List[str]:
    """
    Upload multiple local files to an S3 bucket.
    Returns a list of S3 URIs for the uploaded files.
    """
    s3_uris = []
    for file_path in local_file_paths:
        filename = os.path.basename(file_path)
        key = f"{prefix.rstrip('/')}/{filename}" if prefix else filename
        s3_uri = upload_to_s3(file_path, bucket, key)
        s3_uris.append(s3_uri)
    return s3_uris


def download_json_from_s3(uri: str) -> Dict[Any, Any]:
    """
    Download and parse a JSON file from S3.
    
    Args:
        uri: S3 URI (s3://bucket/key) pointing to a JSON file
        
    Returns:
        dict: Parsed JSON content
        
    Raises:
        ValueError: If the URI is not a valid S3 URI
        ClientError: If the object doesn't exist or access is denied
        json.JSONDecodeError: If the file content is not valid JSON
    """
    bucket, key = parse_s3_uri(uri)
    s3 = get_s3_client()
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise ClientError(
                error_response={'Error': {'Code': 'NoSuchKey', 'Message': f'Object not found: {uri}'}},
                operation_name='GetObject'
            )
        elif error_code == 'AccessDenied':
            raise ClientError(
                error_response={'Error': {'Code': 'AccessDenied', 'Message': f'Access denied to object: {uri}'}},
                operation_name='GetObject'
            )
        else:
            raise

def download_text_from_s3(uri: str) -> str:
    """
    Download a text file from S3.
    
    Args:
        uri: S3 URI (s3://bucket/key) pointing to a text file
        
    Returns:
        str: File content as string
        
    Raises:
        ValueError: If the URI is not a valid S3 URI
        ClientError: If the object doesn't exist or access is denied
    """
    bucket, key = parse_s3_uri(uri)
    s3 = get_s3_client()
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return content
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise ClientError(
                error_response={'Error': {'Code': 'NoSuchKey', 'Message': f'Object not found: {uri}'}},
                operation_name='GetObject'
            )
        elif error_code == 'AccessDenied':
            raise ClientError(
                error_response={'Error': {'Code': 'AccessDenied', 'Message': f'Access denied to object: {uri}'}},
                operation_name='GetObject'
            )
        else:
            raise

def list_s3_objects(bucket: str, prefix: str) -> List[str]:
    """Return full S3 URIs for objects under the given prefix."""
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [f"s3://{bucket}/{obj['Key']}" for obj in response.get("Contents", [])]

def generate_presigned_url(bucket: str, key: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for S3 object access.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        expiration: URL expiration time in seconds (default 1 hour)
        
    Returns:
        Presigned URL string
    """
    try:
        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        logger.info("Generated presigned URL", bucket=bucket, key=key, expiration=expiration)
        return url
        
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {str(e)}", bucket=bucket, key=key)
        raise