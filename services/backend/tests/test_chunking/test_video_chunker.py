"""
Tests for VideoChunker - chunk calculation, FFmpeg operations
"""
import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock, call
from botocore.exceptions import ClientError

from services.chunking.video_chunker import VideoChunker
from schemas.analysis import ChunkInfo, AnalysisConfig, VideoType, AnalysisGoal
from models import ProcessingJob


class TestVideoChunker:
    """Test suite for VideoChunker"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client"""
        return Mock()
    
    @pytest.fixture
    def chunker(self, mock_s3_client, temp_dir):
        """Create VideoChunker instance with mocked dependencies"""
        return VideoChunker(s3_client=mock_s3_client, temp_dir=temp_dir)
    
    @pytest.fixture
    def sample_config(self):
        """Create sample analysis configuration"""
        return AnalysisConfig(
            user_prompt="Analyze this video",
            video_type=VideoType.GENERAL,
            analysis_goals=[AnalysisGoal.SCENE_DETECTION],
            selected_providers={},
            chunk_duration=10,
            chunk_overlap=2,
            cost_estimate=0.5
        )
    
    def test_init(self, chunker, mock_s3_client, temp_dir):
        """Test VideoChunker initialization"""
        assert chunker.s3_client == mock_s3_client
        assert chunker.temp_base_dir == temp_dir
        assert chunker.current_temp_dir is None
    
    def test_parse_s3_uri_valid(self, chunker):
        """Test parsing valid S3 URI"""
        s3_uri = "s3://test-bucket/path/to/video.mp4"
        bucket, key = chunker._parse_s3_uri(s3_uri)
        
        assert bucket == "test-bucket"
        assert key == "path/to/video.mp4"
    
    def test_download_video_invalid_uri(self, chunker):
        """Test download with invalid S3 URI"""
        chunker.current_temp_dir = tempfile.mkdtemp()
        
        with pytest.raises(ValueError, match="Invalid S3 URI"):
            chunker._download_video("http://example.com/video.mp4")
        
        with pytest.raises(ValueError, match="Invalid S3 URI format"):
            chunker._download_video("s3://bucket-only")
        
        # Cleanup
        shutil.rmtree(chunker.current_temp_dir)
    
    def test_download_video_success(self, chunker, mock_s3_client):
        """Test successful video download"""
        chunker.current_temp_dir = tempfile.mkdtemp()
        s3_uri = "s3://test-bucket/videos/test.mp4"
        
        local_path = chunker._download_video(s3_uri)
        
        # Check S3 client was called correctly
        mock_s3_client.download_file.assert_called_once_with(
            "test-bucket",
            "videos/test.mp4",
            local_path
        )
        
        # Check path is in temp directory
        assert local_path.startswith(chunker.current_temp_dir)
        assert local_path.endswith("source_video.mp4")
        
        # Cleanup
        shutil.rmtree(chunker.current_temp_dir)
    
    def test_download_video_s3_error(self, chunker, mock_s3_client):
        """Test video download with S3 error"""
        chunker.current_temp_dir = tempfile.mkdtemp()
        mock_s3_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey"}}, 
            "GetObject"
        )
        
        with pytest.raises(ClientError):
            chunker._download_video("s3://test-bucket/missing.mp4")
        
        # Cleanup
        shutil.rmtree(chunker.current_temp_dir)
    
    @patch('ffmpeg.probe')
    def test_get_video_info_success(self, mock_probe, chunker):
        """Test getting video information"""
        mock_probe.return_value = {
            'format': {'duration': '120.5'},
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'avg_frame_rate': '30/1',
                'codec_name': 'h264'
            }]
        }
        
        info = chunker._get_video_info("/path/to/video.mp4")
        
        assert info['duration'] == 120.5
        assert info['width'] == 1920
        assert info['height'] == 1080
        assert info['fps'] == 30.0
        assert info['codec'] == 'h264'
    
    @patch('ffmpeg.probe')
    def test_get_video_info_no_video_stream(self, mock_probe, chunker):
        """Test getting video info when no video stream exists"""
        mock_probe.return_value = {
            'format': {'duration': '120.5'},
            'streams': [{
                'codec_type': 'audio',
                'codec_name': 'aac'
            }]
        }
        
        with pytest.raises(ValueError, match="No video stream found"):
            chunker._get_video_info("/path/to/audio.mp3")
    
    @patch('ffmpeg.probe')
    def test_get_video_info_ffmpeg_error(self, mock_probe, chunker):
        """Test handling FFmpeg probe errors"""
        import ffmpeg
        mock_probe.side_effect = ffmpeg.Error('stderr', 'stdout')
        
        with pytest.raises(ffmpeg.Error):
            chunker._get_video_info("/path/to/video.mp4")
    
    def test_create_chunks_normal(self, chunker):
        """Test creating chunks for normal video"""
        chunks = chunker._create_chunks(
            video_path="/path/to/video.mp4",
            duration=60.0,
            chunk_duration=10,
            overlap=2
        )
        
        expected = [
            (0.0, 10.0),
            (8.0, 18.0),
            (16.0, 26.0),
            (24.0, 34.0),
            (32.0, 42.0),
            (40.0, 50.0),
            (48.0, 58.0),
            (56.0, 60.0)
        ]
        
        assert chunks == expected
    
    def test_create_chunks_no_overlap(self, chunker):
        """Test creating chunks without overlap"""
        chunks = chunker._create_chunks(
            video_path="/path/to/video.mp4",
            duration=30.0,
            chunk_duration=10,
            overlap=0
        )
        
        expected = [
            (0.0, 10.0),
            (10.0, 20.0),
            (20.0, 30.0)
        ]
        
        assert chunks == expected
    
    def test_create_chunks_tiny_last_chunk(self, chunker):
        """Test handling tiny last chunk"""
        chunks = chunker._create_chunks(
            video_path="/path/to/video.mp4",
            duration=32.0,  # Would create 2-second last chunk
            chunk_duration=10,
            overlap=0
        )
        
        # Should extend last chunk instead of creating tiny one
        expected = [
            (0.0, 10.0),
            (10.0, 20.0),
            (20.0, 32.0)  # Extended to include the tiny remainder
        ]
        
        assert chunks == expected
    
    def test_create_chunks_short_video(self, chunker):
        """Test chunking very short video"""
        chunks = chunker._create_chunks(
            video_path="/path/to/video.mp4",
            duration=5.0,
            chunk_duration=10,
            overlap=2
        )
        
        expected = [(0.0, 5.0)]
        assert chunks == expected
    
    def test_upload_to_s3_success(self, chunker, mock_s3_client):
        """Test successful S3 upload"""
        local_path = "/tmp/test.mp4"
        bucket = "test-bucket"
        key = "videos/test.mp4"
        
        result = chunker._upload_to_s3(local_path, bucket, key)
        
        mock_s3_client.upload_file.assert_called_once_with(local_path, bucket, key)
        assert result == f"s3://{bucket}/{key}"
    
    def test_upload_to_s3_error(self, chunker, mock_s3_client):
        """Test S3 upload error"""
        mock_s3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}},
            "PutObject"
        )
        
        with pytest.raises(ClientError):
            chunker._upload_to_s3("/tmp/test.mp4", "bucket", "key")
    
    @patch('ffmpeg.input')
    def test_process_chunk_success(self, mock_ffmpeg_input, chunker, mock_s3_client):
        """Test processing a single chunk"""
        chunker.current_temp_dir = tempfile.mkdtemp()
        
        # Setup FFmpeg mocks
        mock_stream = MagicMock()
        mock_ffmpeg_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        
        # Mock S3 uploads
        mock_s3_client.upload_file.return_value = None
        
        chunk_info = chunker._process_chunk(
            video_path="/tmp/video.mp4",
            chunk_index=0,
            start_time=0.0,
            end_time=10.0,
            original_s3_uri="s3://bucket/videos/original.mp4"
        )
        
        # Verify chunk info
        assert chunk_info.chunk_id == "chunk_0000"
        assert chunk_info.chunk_index == 0
        assert chunk_info.start_time == 0.0
        assert chunk_info.end_time == 10.0
        assert chunk_info.duration == 10.0
        assert chunk_info.s3_uri.startswith("s3://bucket/videos/original/chunks/")
        assert chunk_info.keyframe_path.startswith("s3://bucket/videos/original/keyframes/")
        
        # Verify FFmpeg was called
        assert mock_ffmpeg_input.call_count == 2  # Once for chunk, once for keyframe
        
        # Cleanup
        shutil.rmtree(chunker.current_temp_dir)
    
    @patch('ffmpeg.input')
    def test_process_chunk_keyframe_error(self, mock_ffmpeg_input, chunker, mock_s3_client):
        """Test chunk processing when keyframe extraction fails"""
        chunker.current_temp_dir = tempfile.mkdtemp()
        
        # Setup FFmpeg mocks - first call succeeds, second fails
        mock_stream = MagicMock()
        mock_ffmpeg_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        
        # Make keyframe extraction fail
        import ffmpeg
        mock_stream.run.side_effect = [None, ffmpeg.Error('stderr', 'stdout')]
        
        chunk_info = chunker._process_chunk(
            video_path="/tmp/video.mp4",
            chunk_index=0,
            start_time=0.0,
            end_time=10.0,
            original_s3_uri="s3://bucket/videos/original.mp4"
        )
        
        # Should still return chunk info but without keyframe
        assert chunk_info.chunk_id == "chunk_0000"
        assert chunk_info.keyframe_path is None
        
        # Cleanup
        shutil.rmtree(chunker.current_temp_dir)
    
    @patch('services.chunking.video_chunker.VideoChunker._get_video_info')
    @patch('services.chunking.video_chunker.VideoChunker._download_video')
    @patch('services.chunking.video_chunker.VideoChunker._process_chunk')
    def test_process_video_complete(self, mock_process_chunk, mock_download, 
                                   mock_get_info, chunker, sample_config):
        """Test complete video processing flow"""
        # Setup mocks
        mock_download.return_value = "/tmp/video.mp4"
        mock_get_info.return_value = {
            'duration': 30.0,
            'width': 1920,
            'height': 1080,
            'fps': 30.0
        }
        
        mock_chunk_info = ChunkInfo(
            chunk_id="chunk_0000",
            chunk_index=0,
            start_time=0.0,
            end_time=10.0,
            duration=10.0,
            s3_uri="s3://bucket/chunk.mp4"
        )
        mock_process_chunk.return_value = mock_chunk_info
        
        # Process video
        chunks = chunker.process_video(
            "s3://bucket/video.mp4",
            sample_config
        )
        
        # Verify results
        assert len(chunks) > 0
        assert mock_download.called
        assert mock_get_info.called
        assert mock_process_chunk.called
    
    @patch('services.chunking.video_chunker.VideoChunker._download_video')
    def test_process_video_with_job_tracking(self, mock_download, chunker, sample_config):
        """Test video processing with job progress tracking"""
        mock_job = Mock(spec=ProcessingJob)
        mock_job.progress = 0
        mock_job.current_step = ""
        
        mock_download.side_effect = Exception("Download failed")
        
        with pytest.raises(Exception):
            chunker.process_video(
                "s3://bucket/video.mp4",
                sample_config,
                mock_job
            )
        
        # Verify job was updated
        assert mock_job.progress == 10
        assert mock_job.current_step == "Downloading video"
    
    def test_cleanup(self, chunker):
        """Test cleanup of temporary files"""
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        chunker.current_temp_dir = temp_dir
        
        # Create some files
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Verify directory exists
        assert os.path.exists(temp_dir)
        
        # Cleanup
        chunker.cleanup()
        
        # Verify directory is removed
        assert not os.path.exists(temp_dir)
        assert chunker.current_temp_dir is None
    
    def test_cleanup_already_deleted(self, chunker):
        """Test cleanup when directory already deleted"""
        chunker.current_temp_dir = "/tmp/non_existent_dir"
        
        # Should not raise exception
        chunker.cleanup()
        
        assert chunker.current_temp_dir is None
    
    def test_cleanup_permission_error(self, chunker):
        """Test cleanup with permission error"""
        with patch('shutil.rmtree') as mock_rmtree:
            mock_rmtree.side_effect = PermissionError("Access denied")
            chunker.current_temp_dir = "/tmp/test"
            
            # Should log warning but not raise
            chunker.cleanup()
            
            assert chunker.current_temp_dir is None