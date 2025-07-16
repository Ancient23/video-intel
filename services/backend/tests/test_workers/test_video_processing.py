"""
Test video processing Celery tasks
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from workers.video_processing import process_video_full_pipeline
from models.video import VideoStatus
from models.processing_job import ProcessingJob, JobStatus


@pytest.mark.unit
class TestVideoProcessingTasks:
    """Test video processing Celery tasks"""
    
    @patch('workers.video_processing.ProcessingJob.get')
    @patch('workers.video_processing.Video.get')
    @patch('workers.video_processing.analyze_video_with_providers')
    def test_process_video_full_pipeline_success(
        self,
        mock_analyze,
        mock_video_get,
        mock_job_get
    ):
        """Test successful video processing pipeline"""
        # Mock video and job
        mock_video = Mock()
        mock_video.id = "video123"
        mock_video.title = "Test Video"
        mock_video.s3_url = "s3://test-bucket/test-video.mp4"
        mock_video.duration = 120.0
        mock_video.save = AsyncMock()
        mock_video.mark_processing = Mock()
        mock_video.mark_completed = Mock()
        mock_video_get.return_value = mock_video
        
        mock_job = Mock(spec=ProcessingJob)
        mock_job.id = "job123"
        mock_job.job_id = "job123"
        mock_job.save = AsyncMock()
        mock_job.start = Mock()
        mock_job.update_progress = Mock()
        mock_job.complete = Mock()
        mock_job_get.return_value = mock_job
        
        # Mock analysis results
        mock_analyze.delay.return_value = Mock(id="analysis-task-123")
        
        # Test configuration
        analysis_config = {
            "providers": ["aws_rekognition", "openai_vision"],
            "chunk_duration": 30.0,
            "analysis_goals": ["scene_detection", "object_detection"]
        }
        
        # Run the task
        result = process_video_full_pipeline(
            "job123",
            "video123",
            analysis_config
        )
        
        # Verify the job was started
        mock_job.start.assert_called_once()
        
        # Verify video status was updated
        mock_video.mark_processing.assert_called_once()
        
        # Verify analysis was triggered
        mock_analyze.delay.assert_called_once()
        
        # Verify result structure
        assert result["status"] == "processing"
        assert result["video_id"] == "video123"
        assert result["job_id"] == "job123"
        assert "analysis_task_id" in result
    
    @patch('workers.video_processing.ProcessingJob.get')
    @patch('workers.video_processing.Video.get')
    def test_process_video_full_pipeline_video_not_found(
        self,
        mock_video_get,
        mock_job_get
    ):
        """Test pipeline with video not found"""
        mock_video_get.return_value = None
        mock_job = Mock(spec=ProcessingJob)
        mock_job.fail = Mock()
        mock_job.save = AsyncMock()
        mock_job_get.return_value = mock_job
        
        # Run the task and expect it to fail
        with pytest.raises(ValueError, match="Video .* not found"):
            process_video_full_pipeline(
                "job123",
                "invalid_id",
                {"providers": []}
            )
    
    @patch('workers.video_processing.ProcessingJob.get')
    @patch('workers.video_processing.Video.get')
    @patch('workers.video_processing.validate_analysis_config')
    def test_process_video_full_pipeline_config_error(
        self,
        mock_validate,
        mock_video_get,
        mock_job_get
    ):
        """Test pipeline with chunking error"""
        mock_video = Mock()
        mock_video.id = "video123"
        mock_video_get.return_value = mock_video
        
        mock_job = Mock(spec=ProcessingJob)
        mock_job.fail = Mock()
        mock_job.save = AsyncMock()
        mock_job_get.return_value = mock_job
        
        # Mock validation failure
        mock_validate.side_effect = ValueError("Invalid configuration")
        
        # Run the task and expect it to handle the error
        with pytest.raises(ValueError, match="Invalid configuration"):
            process_video_full_pipeline(
                "job123",
                "video123",
                {"invalid": "config"}
            )