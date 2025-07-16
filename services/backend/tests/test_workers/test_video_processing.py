"""
Test video processing Celery tasks
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from workers.video_processing import process_video_full_pipeline
from models.video import VideoStatus
from models.processing_job import JobStatus


@pytest.mark.unit
class TestVideoProcessingTasks:
    """Test video processing Celery tasks"""
    
    @patch('workers.video_processing.process_video_chunking')
    @patch('workers.video_processing.run_parallel_analysis')
    @patch('workers.video_processing.aggregate_analysis_results')
    @patch('models.video.Video.get')
    @patch('models.processing_job.ProcessingJob.get')
    def test_process_video_full_pipeline_success(
        self,
        mock_job_get,
        mock_video_get,
        mock_aggregate,
        mock_analysis,
        mock_chunking
    ):
        """Test successful video processing pipeline"""
        # Mock video and job
        mock_video = Mock()
        mock_video.id = "video123"
        mock_video.title = "Test Video"
        mock_video.save = AsyncMock()
        mock_video_get.return_value = mock_video
        
        mock_job = Mock()
        mock_job.id = "job123"
        mock_job.save = AsyncMock()
        mock_job_get.return_value = mock_job
        
        # Mock subtask results
        mock_chunking.return_value = {
            "chunks": ["chunk1", "chunk2"],
            "metadata": {"total_chunks": 2}
        }
        mock_analysis.return_value = {
            "results": ["analysis1", "analysis2"]
        }
        mock_aggregate.return_value = {
            "aggregated": True,
            "summary": "Test summary"
        }
        
        # Mock the task itself
        task = Mock()
        task.request.id = "task123"
        task.update_state = Mock()
        
        # Run the task
        result = process_video_full_pipeline.run(
            "video123",
            "job123",
            ["aws_rekognition", "openai_vision"]
        )
        
        # Verify the pipeline was executed
        assert result["status"] == "completed"
        assert result["video_id"] == "video123"
        assert "chunks" in result
        assert "analysis" in result
        assert "aggregated" in result
    
    @patch('models.video.Video.get')
    @patch('models.processing_job.ProcessingJob.get')
    def test_process_video_full_pipeline_video_not_found(
        self,
        mock_job_get,
        mock_video_get
    ):
        """Test pipeline with video not found"""
        mock_video_get.return_value = None
        mock_job = Mock()
        mock_job.save = AsyncMock()
        mock_job_get.return_value = mock_job
        
        # Run the task and expect it to fail
        with pytest.raises(ValueError, match="Video not found"):
            process_video_full_pipeline.run("invalid_id", "job123", [])
    
    @patch('workers.video_processing.process_video_chunking')
    @patch('models.video.Video.get')
    @patch('models.processing_job.ProcessingJob.get')
    def test_process_video_full_pipeline_chunking_error(
        self,
        mock_job_get,
        mock_video_get,
        mock_chunking
    ):
        """Test pipeline with chunking error"""
        mock_video = Mock()
        mock_video.save = AsyncMock()
        mock_video_get.return_value = mock_video
        
        mock_job = Mock()
        mock_job.save = AsyncMock()
        mock_job_get.return_value = mock_job
        
        # Mock chunking failure
        mock_chunking.side_effect = Exception("Chunking failed")
        
        # Run the task and expect it to handle the error
        with pytest.raises(Exception, match="Chunking failed"):
            process_video_full_pipeline.run("video123", "job123", [])