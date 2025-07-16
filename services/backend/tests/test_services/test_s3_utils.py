"""
Test S3 utilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from services.s3_utils import (
    parse_s3_uri, is_s3_uri, check_s3_object_exists,
    download_from_s3, upload_to_s3, upload_content_to_s3,
    generate_presigned_url, get_s3_client
)
import os


@pytest.mark.unit
class TestS3Utils:
    """Test S3 utilities functionality"""
    
    def test_parse_s3_uri_valid(self):
        """Test parsing valid S3 URIs"""
        # Test standard S3 URI
        bucket, key = parse_s3_uri("s3://my-bucket/path/to/file.mp4")
        assert bucket == "my-bucket"
        assert key == "path/to/file.mp4"
        
        # Test with special characters
        bucket, key = parse_s3_uri("s3://bucket-name/folder/file with spaces.mp4")
        assert bucket == "bucket-name"
        assert key == "folder/file with spaces.mp4"
    
    def test_parse_s3_uri_invalid(self):
        """Test parsing invalid S3 URIs"""
        # Test non-S3 URI
        with pytest.raises(ValueError, match="Not an S3 URI"):
            parse_s3_uri("https://example.com/file.mp4")
        
        # Test empty string
        with pytest.raises(ValueError, match="Not an S3 URI"):
            parse_s3_uri("")
    
    def test_is_s3_uri(self):
        """Test S3 URI detection"""
        assert is_s3_uri("s3://bucket/key") is True
        assert is_s3_uri("https://example.com") is False
        assert is_s3_uri("") is False
        assert is_s3_uri(None) is False
    
    @patch('services.s3_utils.get_s3_client')
    def test_upload_file_success(self, mock_get_s3_client):
        """Test successful file upload"""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        
        # Create a temporary test file
        test_file = "/tmp/test_upload.txt"
        with open(test_file, "w") as f:
            f.write("test content")
        
        try:
            # Test upload
            s3_uri = upload_to_s3(
                test_file,
                "test-bucket",
                "test-folder/test_upload.txt"
            )
            
            assert s3_uri == "s3://test-bucket/test-folder/test_upload.txt"
            mock_s3_client.upload_file.assert_called_once_with(
                test_file,
                "test-bucket",
                "test-folder/test_upload.txt"
            )
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    @patch('services.s3_utils.get_s3_client')
    def test_upload_file_error(self, mock_get_s3_client):
        """Test file upload with S3 error"""
        # Mock S3 client with error
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_s3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "upload_file"
        )
        
        # Create a temporary test file
        test_file = "/tmp/test_upload_error.txt"
        with open(test_file, "w") as f:
            f.write("test content")
        
        try:
            # Test upload failure
            with pytest.raises(ClientError):
                upload_to_s3(
                    test_file,
                    "test-bucket",
                    "test-folder/test_upload_error.txt"
                )
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    @patch('services.s3_utils.get_s3_client')
    def test_download_file_success(self, mock_get_s3_client):
        """Test successful file download"""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        
        # Test download
        local_path = "/tmp/test_download.mp4"
        result = download_from_s3(
            "s3://test-bucket/videos/test.mp4",
            local_path
        )
        
        assert result == local_path
        mock_s3_client.download_file.assert_called_once_with(
            "test-bucket",
            "videos/test.mp4",
            local_path
        )
    
    @patch('services.s3_utils.get_s3_client')
    def test_check_file_exists(self, mock_get_s3_client):
        """Test checking if file exists in S3"""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        
        # Test file exists
        mock_s3_client.head_object.return_value = {"ContentLength": 1024}
        exists = check_s3_object_exists("test-bucket", "exists.mp4")
        assert exists is True
        
        # Reset mock for next test
        mock_s3_client.reset_mock()
        
        # Test file doesn't exist
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "head_object"
        )
        exists = check_s3_object_exists("test-bucket", "not-exists.mp4")
        assert exists is False
    
    @patch('services.s3_utils.get_s3_client')
    def test_generate_presigned_url(self, mock_get_s3_client):
        """Test generating presigned URL"""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_get_s3_client.return_value = mock_s3_client
        mock_s3_client.generate_presigned_url.return_value = "https://presigned-url"
        
        url = generate_presigned_url(
            "test-bucket",
            "video.mp4",
            expiration=3600
        )
        
        assert url == "https://presigned-url"
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': 'video.mp4'},
            ExpiresIn=3600
        )