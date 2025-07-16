"""
Integration tests for API-Celery workflow.

Tests the complete flow from API endpoint to Celery task execution.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from beanie import PydanticObjectId
from httpx import AsyncClient
from celery.result import AsyncResult

from models.video import Video, VideoStatus
from models.processing_job import ProcessingJob, JobStatus, JobType
# from models.video_analysis_job import VideoAnalysisJob, AnalysisStatus  # TODO: Create this model
from schemas.analysis import ProviderType, AnalysisGoal


@pytest.mark.asyncio
class TestAPICeleryIntegration:
    """Test API-Celery integration for video analysis."""
    
    async def test_start_video_analysis_triggers_celery_task(
        self,
        async_client: AsyncClient,
        mock_current_user,
        sample_video_data
    ):
        """Test that API endpoint properly triggers Celery task."""
        # Mock Celery task
        with patch('backend.workers.video_processing.process_video_full_pipeline.apply_async') as mock_task:
            mock_result = MagicMock(spec=AsyncResult)
            mock_result.id = "test-task-123"
            mock_task.return_value = mock_result
            
            # Make API request
            response = await async_client.post(
                "/api/v1/video-analysis/analyze",
                json={
                    "video_url": "s3://test-bucket/test-video.mp4",
                    "user_prompt": "Analyze this video for scene changes and objects",
                    "video_type": "general",
                    "chunk_duration": 30.0,
                    "cost_limit": 10.0
                }
            )
            
            assert response.status_code == 202
            data = response.json()
            
            # Verify response
            assert "job_id" in data
            assert "video_id" in data
            assert data["status"] == "pending"
            assert data["estimated_cost"] > 0
            
            # Verify Celery task was called
            mock_task.assert_called_once()
            args, kwargs = mock_task.call_args
            
            # Check task arguments
            assert len(args[0]) == 3  # job_id, video_id, config
            assert args[0][0] == data["job_id"]
            assert args[0][1] == data["video_id"]
            assert isinstance(args[0][2], dict)  # analysis_config
            
            # Check task options
            assert kwargs["queue"] == "orchestration"
            assert kwargs["task_id"] == f"{data['job_id']}-pipeline"
            assert kwargs["retry"] is True
    
    async def test_job_status_reflects_celery_progress(
        self,
        async_client: AsyncClient,
        mock_current_user
    ):
        """Test that job status endpoint reflects Celery task progress."""
        # Create a job
        job = ProcessingJob(
            job_type=JobType.FULL_PIPELINE,
            video_id="507f1f77bcf86cd799439011",
            provider="multi-provider",
            status=JobStatus.RUNNING,
            progress=50,
            current_step="Analyzing with AWS Rekognition",
            metadata={"celery_task_id": "test-task-456"}
        )
        await job.save()
        
        # Get job status
        response = await async_client.get(f"/api/v1/video-analysis/jobs/{job.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == str(job.id)
        assert data["status"] == "running"
        assert data["progress"] == 50
        assert data["current_step"] == "Analyzing with AWS Rekognition"
    
    async def test_celery_task_updates_job_progress(
        self,
        celery_app,
        celery_worker,
        mongodb_client
    ):
        """Test that Celery task properly updates job progress in MongoDB."""
        from backend.workers.video_processing import update_job_progress
        
        # Create test job
        job = ProcessingJob(
            job_type=JobType.FULL_PIPELINE,
            video_id="507f1f77bcf86cd799439011",
            provider="multi-provider",
            status=JobStatus.RUNNING,
            progress=0
        )
        await job.save()
        
        # Create analysis job
        analysis_job = VideoAnalysisJob(
            processing_job_id=str(job.id),
            video_id=job.video_id,
            user_prompt="Test analysis",
            status=AnalysisStatus.PROCESSING,
            progress=0
        )
        await analysis_job.save()
        
        # Execute task
        result = update_job_progress.apply_async(
            args=[str(job.id), 75, "Merging results", {"stage": "final"}]
        )
        
        # Wait for task completion
        task_result = result.get(timeout=10)
        
        # Verify updates
        updated_job = await ProcessingJob.get(job.id)
        assert updated_job.progress == 75
        assert updated_job.current_step == "Merging results"
        assert updated_job.metadata["stage"] == "final"
        
        updated_analysis = await VideoAnalysisJob.get(analysis_job.id)
        assert updated_analysis.progress == 75
        assert updated_analysis.current_stage == "Merging results"
    
    async def test_full_pipeline_workflow(
        self,
        async_client: AsyncClient,
        mock_current_user,
        celery_app,
        celery_worker
    ):
        """Test complete workflow from API to task completion."""
        # Mock provider analysis tasks
        with patch('backend.workers.video_analysis_tasks.analyze_with_rekognition') as mock_aws, \
             patch('backend.workers.video_analysis_tasks.validate_and_extract_metadata') as mock_validate, \
             patch('backend.workers.ingestion_tasks.chunk_video') as mock_chunk:
            
            # Setup mock returns
            mock_validate.return_value = {"duration": 120.0, "fps": 30.0}
            mock_chunk.return_value = {"chunks": ["chunk1", "chunk2"]}
            mock_aws.return_value = {
                "success": True,
                "provider": "aws_rekognition",
                "chunks": {
                    "chunk1": {"scenes": [{"start": 0, "end": 30}]},
                    "chunk2": {"scenes": [{"start": 30, "end": 60}]}
                }
            }
            
            # Start analysis via API
            response = await async_client.post(
                "/api/v1/video-analysis/analyze",
                json={
                    "video_url": "s3://test-bucket/test-video.mp4",
                    "user_prompt": "Find all scene changes",
                    "selected_providers": ["aws_rekognition"]
                }
            )
            
            assert response.status_code == 202
            job_id = response.json()["job_id"]
            
            # Wait for task to complete (with timeout)
            import asyncio
            for _ in range(20):  # 10 seconds max
                job = await ProcessingJob.get(job_id)
                if job.status == JobStatus.COMPLETED:
                    break
                await asyncio.sleep(0.5)
            
            # Verify final state
            assert job.status == JobStatus.COMPLETED
            assert job.progress == 100
            assert job.result is not None
    
    async def test_retry_failed_job(
        self,
        async_client: AsyncClient,
        mock_current_user
    ):
        """Test retrying a failed job via API."""
        # Create failed job
        job = ProcessingJob(
            job_type=JobType.FULL_PIPELINE,
            video_id="507f1f77bcf86cd799439011",
            provider="multi-provider",
            status=JobStatus.FAILED,
            error_message="Provider timeout",
            retry_count=1,
            config={"analysis_config": {"chunk_duration": 30}}
        )
        await job.save()
        
        # Mock Celery task
        with patch('backend.workers.video_processing.process_video_full_pipeline.apply_async') as mock_task:
            mock_result = MagicMock(spec=AsyncResult)
            mock_result.id = "retry-task-789"
            mock_task.return_value = mock_result
            
            # Retry job
            response = await async_client.post(
                f"/api/v1/video-analysis/jobs/{job.id}/retry",
                json={"force": False}
            )
            
            assert response.status_code == 202
            data = response.json()
            
            assert data["job_id"] == str(job.id)
            assert "retry started" in data["message"]
            
            # Verify task was triggered
            mock_task.assert_called_once()
            
            # Verify job status updated
            updated_job = await ProcessingJob.get(job.id)
            assert updated_job.status == JobStatus.PENDING
            assert updated_job.retry_count == 2
    
    async def test_concurrent_job_prevention(
        self,
        async_client: AsyncClient,
        mock_current_user
    ):
        """Test that concurrent jobs for same video are prevented."""
        # Create video with running job
        video = Video(
            title="test.mp4",
            s3_url="s3://test-bucket/test.mp4",
            status=VideoStatus.PROCESSING
        )
        await video.save()
        
        job = ProcessingJob(
            job_type=JobType.FULL_PIPELINE,
            video_id=str(video.id),
            provider="multi-provider",
            status=JobStatus.RUNNING
        )
        await job.save()
        
        # Try to start another analysis
        response = await async_client.post(
            "/api/v1/video-analysis/analyze",
            json={
                "video_url": "s3://test-bucket/test.mp4",
                "user_prompt": "Another analysis"
            }
        )
        
        assert response.status_code == 409
        assert "already has a running job" in response.json()["detail"]
    
    async def test_cost_limit_enforcement(
        self,
        async_client: AsyncClient,
        mock_current_user
    ):
        """Test that cost limits are enforced before starting tasks."""
        response = await async_client.post(
            "/api/v1/video-analysis/analyze",
            json={
                "video_url": "s3://test-bucket/expensive-video.mp4",
                "user_prompt": "Analyze everything with all providers",
                "selected_providers": ["openai_gpt4v", "nvidia_vila", "aws_rekognition"],
                "cost_limit": 1.0  # Very low limit
            }
        )
        
        assert response.status_code == 400
        assert "exceeds limit" in response.json()["detail"]


@pytest.fixture
def mock_current_user():
    """Mock current user dependency."""
    with patch('backend.api.v1.routers.video_analysis.get_current_user') as mock:
        mock.return_value = {"user_id": "test-user-123", "role": "user"}
        yield mock


@pytest.fixture
def sample_video_data():
    """Sample video data for tests."""
    return {
        "title": "test_video.mp4",
        "s3_url": "s3://test-bucket/test_video.mp4",
        "duration": 120.0,
        "fps": 30.0,
        "width": 1920,
        "height": 1080
    }