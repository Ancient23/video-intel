"""
Unit tests for NVIDIA VILA S3 download functionality.
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock, call
from botocore.exceptions import ClientError

from services.analysis.providers.nvidia_vila import NvidiaVilaAnalyzer
from schemas.analysis import ChunkInfo, AnalysisConfig, AnalysisGoal


@pytest.fixture
def vila_analyzer():
    """Create NVIDIA VILA analyzer instance."""
    return NvidiaVilaAnalyzer(api_key="test-api-key")


@pytest.fixture
def sample_chunk_s3():
    """Create sample chunk with S3 URI."""
    return ChunkInfo(
        chunk_id="chunk_001",
        video_id="video_123",
        chunk_index=0,
        start_time=0.0,
        end_time=30.0,
        duration=30.0,
        s3_uri="s3://test-bucket/videos/test-video.mp4",
        local_path=None
    )


@pytest.fixture
def sample_chunk_local():
    """Create sample chunk with local path."""
    return ChunkInfo(
        chunk_id="chunk_001",
        video_id="video_123",
        chunk_index=0,
        start_time=0.0,
        end_time=30.0,
        duration=30.0,
        s3_uri=None,
        local_path="/tmp/test-video.mp4"
    )


@pytest.fixture
def analysis_config():
    """Create sample analysis config."""
    return AnalysisConfig(
        analysis_goals=[AnalysisGoal.SCENE_DETECTION, AnalysisGoal.ACTION_DETECTION],
        selected_providers=[],
        chunk_duration=30.0,
        max_frames_per_chunk=10
    )


class TestNvidiaVilaS3Integration:
    """Test S3 integration in NVIDIA VILA provider."""
    
    @pytest.mark.asyncio
    async def test_extract_frames_with_s3_download(self, vila_analyzer, sample_chunk_s3):
        """Test frame extraction with S3 download."""
        # Mock dependencies
        with patch('services.analysis.providers.nvidia_vila.download_from_s3') as mock_download, \
             patch('services.analysis.providers.nvidia_vila.is_s3_uri') as mock_is_s3, \
             patch('services.analysis.providers.nvidia_vila.ffmpeg') as mock_ffmpeg, \
             patch('os.unlink') as mock_unlink:
            
            # Setup mocks
            mock_is_s3.return_value = True
            mock_download.return_value = "/tmp/downloaded-video.mp4"
            
            # Mock ffmpeg frame extraction
            mock_frame_data = b"fake_jpeg_data"
            mock_ffmpeg_stream = MagicMock()
            mock_ffmpeg_stream.run.return_value = (mock_frame_data, None)
            mock_ffmpeg.input.return_value.output.return_value = mock_ffmpeg_stream
            
            # Execute
            frames = await vila_analyzer._extract_frames(sample_chunk_s3, max_frames=5)
            
            # Verify S3 download was called
            mock_is_s3.assert_called_once_with("s3://test-bucket/videos/test-video.mp4")
            mock_download.assert_called_once_with("s3://test-bucket/videos/test-video.mp4")
            
            # Verify cleanup was attempted
            mock_unlink.assert_called_once_with("/tmp/downloaded-video.mp4")
            
            # Verify frames were extracted
            assert len(frames) == 5
            assert all(isinstance(frame, str) for frame in frames)
    
    @pytest.mark.asyncio
    async def test_extract_frames_with_local_path(self, vila_analyzer, sample_chunk_local):
        """Test frame extraction with local path (no S3 download)."""
        with patch('services.analysis.providers.nvidia_vila.ffmpeg') as mock_ffmpeg:
            # Mock ffmpeg
            mock_frame_data = b"fake_jpeg_data"
            mock_ffmpeg_stream = MagicMock()
            mock_ffmpeg_stream.run.return_value = (mock_frame_data, None)
            mock_ffmpeg.input.return_value.output.return_value = mock_ffmpeg_stream
            
            # Execute
            frames = await vila_analyzer._extract_frames(sample_chunk_local, max_frames=3)
            
            # Verify no S3 operations
            assert len(frames) == 3
            # Verify ffmpeg was called with local path
            mock_ffmpeg.input.assert_called_with("/tmp/test-video.mp4", ss=0.0)
    
    @pytest.mark.asyncio
    async def test_s3_download_access_denied(self, vila_analyzer, sample_chunk_s3):
        """Test handling of S3 access denied error."""
        with patch('services.analysis.providers.nvidia_vila.download_from_s3') as mock_download, \
             patch('services.analysis.providers.nvidia_vila.is_s3_uri') as mock_is_s3:
            
            mock_is_s3.return_value = True
            # Simulate S3 access denied
            mock_download.side_effect = ClientError(
                error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
                operation_name='GetObject'
            )
            
            # Execute and expect ValueError
            with pytest.raises(ValueError, match="Access denied to S3 object"):
                await vila_analyzer._extract_frames(sample_chunk_s3, max_frames=5)
    
    @pytest.mark.asyncio
    async def test_s3_download_not_found(self, vila_analyzer, sample_chunk_s3):
        """Test handling of S3 object not found error."""
        with patch('services.analysis.providers.nvidia_vila.download_from_s3') as mock_download, \
             patch('services.analysis.providers.nvidia_vila.is_s3_uri') as mock_is_s3:
            
            mock_is_s3.return_value = True
            # Simulate S3 not found
            mock_download.side_effect = ClientError(
                error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}},
                operation_name='GetObject'
            )
            
            # Execute and expect ValueError
            with pytest.raises(ValueError, match="Video not found in S3"):
                await vila_analyzer._extract_frames(sample_chunk_s3, max_frames=5)
    
    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self, vila_analyzer, sample_chunk_s3):
        """Test that temporary file is cleaned up even on exception."""
        with patch('services.analysis.providers.nvidia_vila.download_from_s3') as mock_download, \
             patch('services.analysis.providers.nvidia_vila.is_s3_uri') as mock_is_s3, \
             patch('services.analysis.providers.nvidia_vila.ffmpeg') as mock_ffmpeg, \
             patch('os.unlink') as mock_unlink, \
             patch('os.path.exists') as mock_exists:
            
            mock_is_s3.return_value = True
            mock_download.return_value = "/tmp/downloaded-video.mp4"
            mock_exists.return_value = True
            
            # Make ffmpeg raise an exception
            mock_ffmpeg.input.side_effect = Exception("FFmpeg failed")
            
            # Execute and expect exception
            with pytest.raises(Exception, match="FFmpeg failed"):
                await vila_analyzer._extract_frames(sample_chunk_s3, max_frames=5)
            
            # Verify cleanup was still called
            mock_unlink.assert_called_once_with("/tmp/downloaded-video.mp4")
    
    @pytest.mark.asyncio
    async def test_invalid_s3_uri(self, vila_analyzer):
        """Test handling of invalid S3 URI."""
        chunk = ChunkInfo(
            chunk_id="chunk_001",
            video_id="video_123",
            chunk_index=0,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            s3_uri="https://not-s3.com/video.mp4",  # Not an S3 URI
            local_path=None
        )
        
        with patch('services.analysis.providers.nvidia_vila.is_s3_uri') as mock_is_s3:
            mock_is_s3.return_value = False
            
            with pytest.raises(ValueError, match="Invalid S3 URI"):
                await vila_analyzer._extract_frames(chunk, max_frames=5)
    
    @pytest.mark.asyncio
    async def test_no_video_path_available(self, vila_analyzer):
        """Test error when neither local nor S3 path is available."""
        chunk = ChunkInfo(
            chunk_id="chunk_001",
            video_id="video_123",
            chunk_index=0,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            s3_uri=None,
            local_path=None
        )
        
        with pytest.raises(ValueError, match="No video path available"):
            await vila_analyzer._extract_frames(chunk, max_frames=5)
    
    @pytest.mark.asyncio
    async def test_full_analysis_with_s3(self, vila_analyzer, sample_chunk_s3, analysis_config):
        """Test full analysis flow with S3 download."""
        with patch('services.analysis.providers.nvidia_vila.download_from_s3') as mock_download, \
             patch('services.analysis.providers.nvidia_vila.is_s3_uri') as mock_is_s3, \
             patch('services.analysis.providers.nvidia_vila.ffmpeg') as mock_ffmpeg, \
             patch('os.unlink') as mock_unlink, \
             patch.object(vila_analyzer, '_call_vila_api') as mock_api:
            
            # Setup mocks
            mock_is_s3.return_value = True
            mock_download.return_value = "/tmp/downloaded-video.mp4"
            
            # Mock ffmpeg
            mock_frame_data = b"fake_jpeg_data"
            mock_ffmpeg_stream = MagicMock()
            mock_ffmpeg_stream.run.return_value = (mock_frame_data, None)
            mock_ffmpeg.input.return_value.output.return_value = mock_ffmpeg_stream
            
            # Mock API response
            mock_api.return_value = {
                "choices": [{
                    "message": {
                        "content": "Scene 1: Action sequence detected"
                    }
                }],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50
                }
            }
            
            # Execute full analysis
            result = await vila_analyzer.analyze_chunk(sample_chunk_s3, analysis_config)
            
            # Verify S3 download happened
            mock_download.assert_called_once()
            
            # Verify cleanup happened
            mock_unlink.assert_called_once()
            
            # Verify result
            assert result.success is True
            assert result.provider == "nvidia_vila"
            assert len(result.scenes) > 0
            assert result.processing_time > 0
            assert result.total_cost > 0