"""
Test S3 utilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from services.s3_utils import S3Service
import os


@pytest.mark.unit
class TestS3Service:
    """Test S3Service functionality"""
    
    def test_parse_s3_uri_valid(self):
        """Test parsing valid S3 URIs"""
        service = S3Service()
        
        # Test standard S3 URI
        bucket, key = service.parse_s3_uri("s3://my-bucket/path/to/file.mp4")
        assert bucket == "my-bucket"
        assert key == "path/to/file.mp4"
        
        # Test with special characters
        bucket, key = service.parse_s3_uri("s3://bucket-name/folder/file with spaces.mp4")
        assert bucket == "bucket-name"
        assert key == "folder/file with spaces.mp4"
    
    def test_parse_s3_uri_invalid(self):
        """Test parsing invalid S3 URIs"""
        service = S3Service()
        
        # Test non-S3 URI
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            service.parse_s3_uri("https://example.com/file.mp4")
        
        # Test missing bucket
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            service.parse_s3_uri("s3://")
        
        # Test missing key
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            service.parse_s3_uri("s3://bucket/")
    
    async def test_upload_file_success(self, mock_boto3_client):
        """Test successful file upload"""
        service = S3Service()
        service.s3_client = mock_boto3_client
        
        # Create a temporary test file
        test_file = "/tmp/test_upload.txt"
        with open(test_file, "w") as f:
            f.write("test content")
        
        try:
            # Test upload
            s3_uri = await service.upload_file(
                test_file,
                "test-bucket",
                "test-folder/test_upload.txt"
            )
            
            assert s3_uri == "s3://test-bucket/test-folder/test_upload.txt"
            mock_boto3_client.upload_file.assert_called_once_with(
                test_file,
                "test-bucket",
                "test-folder/test_upload.txt"
            )
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    async def test_upload_file_error(self, mock_boto3_client):
        """Test file upload with S3 error"""
        service = S3Service()
        service.s3_client = mock_boto3_client
        
        # Mock S3 error
        mock_boto3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "upload_file"
        )
        
        # Create a temporary test file
        test_file = "/tmp/test_upload_error.txt"
        with open(test_file, "w") as f:
            f.write("test content")
        
        try:
            # Test upload failure
            with pytest.raises(Exception, match="Failed to upload"):
                await service.upload_file(
                    test_file,
                    "test-bucket",
                    "test-folder/test_upload_error.txt"
                )
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    async def test_download_file_success(self, mock_boto3_client):
        """Test successful file download"""
        service = S3Service()
        service.s3_client = mock_boto3_client
        
        # Test download
        local_path = "/tmp/test_download.mp4"
        result = await service.download_file(
            "s3://test-bucket/videos/test.mp4",
            local_path
        )
        
        assert result == local_path
        mock_boto3_client.download_file.assert_called_once_with(
            "test-bucket",
            "videos/test.mp4",
            local_path
        )
    
    async def test_check_file_exists(self, mock_boto3_client):
        """Test checking if file exists in S3"""
        service = S3Service()
        service.s3_client = mock_boto3_client
        
        # Test file exists
        mock_boto3_client.head_object.return_value = {"ContentLength": 1024}
        exists = await service.check_file_exists("s3://test-bucket/exists.mp4")
        assert exists is True
        
        # Test file doesn't exist
        mock_boto3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "head_object"
        )
        exists = await service.check_file_exists("s3://test-bucket/not-exists.mp4")
        assert exists is False
    
    async def test_generate_presigned_url(self, mock_boto3_client):
        """Test generating presigned URL"""
        service = S3Service()
        service.s3_client = mock_boto3_client
        
        # Mock presigned URL generation
        mock_boto3_client.generate_presigned_url.return_value = "https://presigned-url"
        
        url = await service.generate_presigned_url(
            "s3://test-bucket/video.mp4",
            expiration=3600
        )
        
        assert url == "https://presigned-url"
        mock_boto3_client.generate_presigned_url.assert_called_once()