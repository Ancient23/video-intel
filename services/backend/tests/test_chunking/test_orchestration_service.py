"""
Tests for VideoChunkingOrchestrationService - main workflow with mocked dependencies
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

from services.chunking.orchestration_service import VideoChunkingOrchestrationService
from services.chunking.analysis_planner import AnalysisPlanner
from services.chunking.video_chunker import VideoChunker
from services.chunking.provider_orchestrator import ProviderOrchestrator
from schemas.analysis import (
    AnalysisConfig, ChunkInfo, AnalysisResult, ProviderType,
    AnalysisGoal, VideoType, SceneDetection, ObjectDetection
)
from models import Video, VideoStatus, Scene, ProcessingJob, JobStatus, JobType


class TestVideoChunkingOrchestrationService:
    """Test suite for VideoChunkingOrchestrationService"""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client"""
        return Mock()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup handled by service
    
    @pytest.fixture
    def orchestration_service(self, mock_s3_client, temp_dir):
        """Create orchestration service with mocked dependencies"""
        service = VideoChunkingOrchestrationService(
            s3_client=mock_s3_client,
            temp_dir=temp_dir,
            s3_output_bucket="test-output-bucket"
        )
        return service
    
    @pytest.fixture
    def mock_video(self):
        """Create mock video document"""
        video = AsyncMock(spec=Video)
        video.id = "test_video_id"
        video.filename = "test_video.mp4"
        video.duration = 120.0
        video.s3_uri = "s3://test-bucket/videos/test.mp4"
        video.status = VideoStatus.UPLOADED
        video.save = AsyncMock()
        return video
    
    @pytest.fixture
    def mock_job(self):
        """Create mock processing job"""
        job = AsyncMock(spec=ProcessingJob)
        job.id = "test_job_id"
        job.video_id = "test_video_id"
        job.status = JobStatus.PENDING
        job.progress = 0
        job.current_step = ""
        job.start = AsyncMock()
        job.save = AsyncMock()
        job.update_progress = AsyncMock()
        job.complete = AsyncMock()
        job.fail = AsyncMock()
        return job
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunk list"""
        return [
            ChunkInfo(
                chunk_id=f"chunk_{i:04d}",
                chunk_index=i,
                start_time=i * 10.0,
                end_time=(i + 1) * 10.0,
                duration=10.0,
                s3_uri=f"s3://test-bucket/chunks/chunk_{i}.mp4",
                keyframe_path=f"s3://test-bucket/keyframes/chunk_{i}.jpg"
            )
            for i in range(3)
        ]
    
    @pytest.fixture
    def sample_analysis_config(self):
        """Create sample analysis configuration"""
        return AnalysisConfig(
            user_prompt="Analyze this video for scenes and objects",
            video_type=VideoType.GENERAL,
            analysis_goals=[AnalysisGoal.SCENE_DETECTION, AnalysisGoal.OBJECT_DETECTION],
            selected_providers={
                AnalysisGoal.SCENE_DETECTION.value: [ProviderType.AWS_REKOGNITION],
                AnalysisGoal.OBJECT_DETECTION.value: [ProviderType.AWS_REKOGNITION]
            },
            chunk_duration=10,
            chunk_overlap=2,
            cost_estimate=0.5
        )
    
    @pytest.fixture
    def sample_analysis_results(self):
        """Create sample analysis results"""
        return [
            AnalysisResult(
                video_id="test_video_id",
                chunk_id=f"chunk_{i:04d}",
                scenes=[
                    SceneDetection(
                        scene_id=f"scene_{i}",
                        start_time=i * 10.0,
                        end_time=(i + 1) * 10.0,
                        scene_type="general",
                        confidence=0.9,
                        description=f"Scene {i}"
                    )
                ],
                objects=[
                    ObjectDetection(
                        label="person",
                        confidence=0.95,
                        frame_time=5.0,
                        bounding_box={"x": 100, "y": 100, "width": 50, "height": 100}
                    )
                ],
                captions=[f"Caption for chunk {i}"],
                custom_analysis={"sentiment": "neutral"},
                provider_metadata={"provider": "aws_rekognition"},
                processing_time=0.5,
                total_cost=0.1
            )
            for i in range(3)
        ]
    
    @pytest.mark.asyncio
    async def test_process_video_success(self, orchestration_service, mock_video, 
                                       mock_job, sample_chunks, sample_analysis_config,
                                       sample_analysis_results):
        """Test successful video processing"""
        # Mock Video.get
        with patch('models.Video.get', AsyncMock(return_value=mock_video)):
            # Mock ProcessingJob.get
            with patch('models.ProcessingJob.get', AsyncMock(return_value=mock_job)):
                # Mock planner
                orchestration_service.analysis_planner.analyze_prompt = Mock(
                    return_value=sample_analysis_config
                )
                
                # Mock chunker
                orchestration_service.video_chunker.process_video = Mock(
                    return_value=sample_chunks
                )
                orchestration_service.video_chunker.cleanup = Mock()
                
                # Mock provider orchestrator
                orchestration_service.provider_orchestrator.orchestrate_analysis = AsyncMock(
                    return_value=sample_analysis_results
                )
                
                # Mock Scene creation
                with patch('models.Scene') as MockScene:
                    mock_scene = AsyncMock()
                    mock_scene.save = AsyncMock()
                    MockScene.return_value = mock_scene
                    
                    result = await orchestration_service.process_video(
                        "test_video_id",
                        "Analyze this video",
                        "test_job_id"
                    )
        
        # Verify result
        assert result["status"] == "success"
        assert result["video_id"] == "test_video_id"
        assert result["chunks_processed"] == 3
        assert result["scenes_created"] == 3
        assert result["total_cost"] == 0.3  # 3 chunks * 0.1
        
        # Verify video status updates
        assert mock_video.status == VideoStatus.ANALYZED
        assert mock_video.processing_started_at is not None
        assert mock_video.processing_completed_at is not None
        assert mock_video.total_scenes == 3
        assert mock_video.save.called
        
        # Verify job updates
        assert mock_job.start.called
        assert mock_job.complete.called
        assert mock_job.save.called
        
        # Verify cleanup
        assert orchestration_service.video_chunker.cleanup.called
    
    @pytest.mark.asyncio
    async def test_process_video_no_job(self, orchestration_service, mock_video,
                                      sample_chunks, sample_analysis_config,
                                      sample_analysis_results):
        """Test video processing without job tracking"""
        with patch('models.Video.get', AsyncMock(return_value=mock_video)):
            orchestration_service.analysis_planner.analyze_prompt = Mock(
                return_value=sample_analysis_config
            )
            orchestration_service.video_chunker.process_video = Mock(
                return_value=sample_chunks
            )
            orchestration_service.video_chunker.cleanup = Mock()
            orchestration_service.provider_orchestrator.orchestrate_analysis = AsyncMock(
                return_value=sample_analysis_results
            )
            
            with patch('models.Scene') as MockScene:
                mock_scene = AsyncMock()
                mock_scene.save = AsyncMock()
                MockScene.return_value = mock_scene
                
                result = await orchestration_service.process_video(
                    "test_video_id",
                    "Analyze this video",
                    None  # No job ID
                )
        
        assert result["status"] == "success"
        assert mock_video.save.called
    
    @pytest.mark.asyncio
    async def test_process_video_not_found(self, orchestration_service):
        """Test processing when video not found"""
        with patch('models.Video.get', AsyncMock(return_value=None)):
            with pytest.raises(ValueError, match="Video test_video_id not found"):
                await orchestration_service.process_video(
                    "test_video_id",
                    "Analyze this video"
                )
    
    @pytest.mark.asyncio
    async def test_process_video_chunking_error(self, orchestration_service, mock_video, mock_job):
        """Test handling chunking errors"""
        with patch('models.Video.get', AsyncMock(return_value=mock_video)):
            with patch('models.ProcessingJob.get', AsyncMock(return_value=mock_job)):
                orchestration_service.analysis_planner.analyze_prompt = Mock(
                    side_effect=Exception("Chunking failed")
                )
                orchestration_service.video_chunker.cleanup = Mock()
                
                with pytest.raises(Exception, match="Chunking failed"):
                    await orchestration_service.process_video(
                        "test_video_id",
                        "Analyze this video",
                        "test_job_id"
                    )
        
        # Verify error handling
        assert mock_video.status == VideoStatus.FAILED
        assert mock_video.error_message == "Chunking failed"
        assert mock_video.save.called
        assert mock_job.fail.called
        assert orchestration_service.video_chunker.cleanup.called
    
    @pytest.mark.asyncio
    async def test_chunk_video(self, orchestration_service, mock_video, 
                             sample_analysis_config, sample_chunks):
        """Test video chunking with async execution"""
        mock_video.save = AsyncMock()
        
        # Mock the run_in_executor to return chunks
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop
            mock_loop.run_in_executor = AsyncMock(return_value=sample_chunks)
            
            chunks = await orchestration_service._chunk_video(
                mock_video, sample_analysis_config, None
            )
        
        assert len(chunks) == 3
        assert mock_video.chunks is not None
        assert len(mock_video.chunks) == 3
        assert mock_video.save.called
    
    def test_merge_overlapping_scenes(self, orchestration_service):
        """Test merging overlapping scene detections"""
        scenes = [
            SceneDetection(
                scene_id="scene_1",
                start_time=0.0,
                end_time=10.0,
                confidence=0.9,
                description="Scene 1"
            ),
            SceneDetection(
                scene_id="scene_2",
                start_time=9.0,  # Overlaps with scene_1
                end_time=15.0,
                confidence=0.95,
                description="Scene 2"
            ),
            SceneDetection(
                scene_id="scene_3",
                start_time=20.0,  # No overlap
                end_time=30.0,
                confidence=0.85,
                description="Scene 3"
            )
        ]
        
        merged = orchestration_service._merge_overlapping_scenes(scenes)
        
        assert len(merged) == 2
        # First merged scene
        assert merged[0].start_time == 0.0
        assert merged[0].end_time == 15.0  # Extended
        assert merged[0].confidence == 0.95  # Max confidence
        assert "Scene 1" in merged[0].description
        assert "Scene 2" in merged[0].description
        # Second scene (no merge)
        assert merged[1].start_time == 20.0
        assert merged[1].end_time == 30.0
    
    def test_merge_overlapping_scenes_close_proximity(self, orchestration_service):
        """Test merging scenes that are very close (within 1 second)"""
        scenes = [
            SceneDetection(
                scene_id="scene_1",
                start_time=0.0,
                end_time=10.0,
                confidence=0.9
            ),
            SceneDetection(
                scene_id="scene_2",
                start_time=10.5,  # Within 1 second of scene_1 end
                end_time=20.0,
                confidence=0.85
            )
        ]
        
        merged = orchestration_service._merge_overlapping_scenes(scenes)
        
        assert len(merged) == 1
        assert merged[0].start_time == 0.0
        assert merged[0].end_time == 20.0
    
    def test_merge_descriptions(self, orchestration_service):
        """Test description merging logic"""
        # Both descriptions exist
        result = orchestration_service._merge_descriptions("Desc 1", "Desc 2")
        assert result == "Desc 1. Desc 2"
        
        # Only first exists
        result = orchestration_service._merge_descriptions("Desc 1", None)
        assert result == "Desc 1"
        
        # Only second exists
        result = orchestration_service._merge_descriptions(None, "Desc 2")
        assert result == "Desc 2"
        
        # Same descriptions
        result = orchestration_service._merge_descriptions("Same", "Same")
        assert result == "Same"
    
    def test_extract_scene_analysis(self, orchestration_service, sample_analysis_results,
                                   sample_chunks):
        """Test extracting analysis data for a specific scene"""
        scene = SceneDetection(
            scene_id="test_scene",
            start_time=5.0,
            end_time=15.0,
            confidence=0.9
        )
        
        analysis_data = orchestration_service._extract_scene_analysis(
            scene, sample_analysis_results, sample_chunks
        )
        
        # Should include data from chunks 0 and 1 (0-10s and 10-20s)
        assert len(analysis_data["objects"]) > 0
        assert len(analysis_data["captions"]) > 0
        assert "sentiment" in analysis_data["custom_analysis"]
        assert "aws_rekognition" in analysis_data["providers"]
    
    @pytest.mark.asyncio
    async def test_create_scenes_with_detections(self, orchestration_service, mock_video,
                                                sample_analysis_results, sample_chunks):
        """Test scene creation from analysis results"""
        mock_video.id = "test_video_id"
        mock_video.duration = 30.0
        
        with patch('models.Scene') as MockScene:
            mock_scene = AsyncMock()
            mock_scene.save = AsyncMock()
            MockScene.return_value = mock_scene
            
            scenes = await orchestration_service._create_scenes(
                mock_video, sample_analysis_results, sample_chunks
            )
        
        assert len(scenes) == 3  # One scene per chunk in this case
        assert MockScene.call_count == 3
    
    @pytest.mark.asyncio
    async def test_create_scenes_no_detections(self, orchestration_service, mock_video,
                                              sample_chunks):
        """Test scene creation when no scenes detected"""
        mock_video.id = "test_video_id"
        mock_video.duration = 30.0
        
        # Analysis results with no scene detections
        empty_results = [
            AnalysisResult(
                video_id="test_video_id",
                chunk_id=f"chunk_{i:04d}",
                scenes=[],  # No scenes
                objects=[],
                provider_metadata={}
            )
            for i in range(3)
        ]
        
        with patch('models.Scene') as MockScene:
            mock_scene = AsyncMock()
            mock_scene.save = AsyncMock()
            MockScene.return_value = mock_scene
            
            scenes = await orchestration_service._create_scenes(
                mock_video, empty_results, sample_chunks
            )
        
        # Should create one scene for entire video
        assert len(scenes) == 1
        assert MockScene.call_count == 1
        # Verify the single scene covers entire video
        call_args = MockScene.call_args[1]
        assert call_args["start_time"] == 0.0
        assert call_args["end_time"] == 30.0
        assert call_args["scene_type"] == "full_video"
    
    @pytest.mark.asyncio
    async def test_retry_failed_job(self, orchestration_service):
        """Test retrying a failed job"""
        mock_job = AsyncMock(spec=ProcessingJob)
        mock_job.id = "test_job_id"
        mock_job.video_id = "test_video_id"
        mock_job.status = JobStatus.FAILED
        mock_job.config = {"user_prompt": "Analyze video"}
        mock_job.retry = Mock(return_value=True)
        mock_job.save = AsyncMock()
        
        mock_video = AsyncMock(spec=Video)
        mock_video.id = "test_video_id"
        
        with patch('models.ProcessingJob.get', AsyncMock(return_value=mock_job)):
            with patch('models.Video.get', AsyncMock(return_value=mock_video)):
                # Mock the process_video method
                orchestration_service.process_video = AsyncMock(
                    return_value={"status": "success"}
                )
                
                result = await orchestration_service.retry_failed_job("test_job_id")
        
        assert result["status"] == "success"
        assert mock_job.retry.called
        assert mock_job.save.called
        orchestration_service.process_video.assert_called_with(
            "test_video_id",
            "Analyze video",
            "test_job_id"
        )
    
    @pytest.mark.asyncio
    async def test_retry_failed_job_not_found(self, orchestration_service):
        """Test retrying non-existent job"""
        with patch('models.ProcessingJob.get', AsyncMock(return_value=None)):
            with pytest.raises(ValueError, match="Job test_job_id not found"):
                await orchestration_service.retry_failed_job("test_job_id")
    
    @pytest.mark.asyncio
    async def test_retry_failed_job_not_failed(self, orchestration_service):
        """Test retrying job that's not in failed state"""
        mock_job = AsyncMock(spec=ProcessingJob)
        mock_job.status = JobStatus.RUNNING
        
        with patch('models.ProcessingJob.get', AsyncMock(return_value=mock_job)):
            with pytest.raises(ValueError, match="not in failed state"):
                await orchestration_service.retry_failed_job("test_job_id")
    
    @pytest.mark.asyncio
    async def test_retry_failed_job_max_retries(self, orchestration_service):
        """Test retrying job that exceeded max retries"""
        mock_job = AsyncMock(spec=ProcessingJob)
        mock_job.status = JobStatus.FAILED
        mock_job.retry = Mock(return_value=False)  # Max retries exceeded
        mock_job.save = AsyncMock()
        
        with patch('models.ProcessingJob.get', AsyncMock(return_value=mock_job)):
            with pytest.raises(ValueError, match="exceeded max retries"):
                await orchestration_service.retry_failed_job("test_job_id")
    
    @pytest.mark.asyncio
    async def test_get_processing_status(self, orchestration_service):
        """Test getting video processing status"""
        mock_video = AsyncMock(spec=Video)
        mock_video.id = "test_video_id"
        mock_video.status = VideoStatus.PROCESSING
        mock_video.total_scenes = 5
        mock_video.processing_started_at = datetime.utcnow()
        mock_video.processing_completed_at = None
        mock_video.error_message = None
        
        mock_job = AsyncMock(spec=ProcessingJob)
        mock_job.id = "test_job_id"
        mock_job.progress = 75
        mock_job.current_step = "Analyzing chunks"
        
        with patch('models.Video.get', AsyncMock(return_value=mock_video)):
            with patch('models.ProcessingJob.find') as mock_find:
                mock_find.return_value.to_list = AsyncMock(return_value=[mock_job])
                
                status = await orchestration_service.get_processing_status("test_video_id")
        
        assert status["video_id"] == "test_video_id"
        assert status["status"] == VideoStatus.PROCESSING
        assert status["progress"] == 75
        assert status["current_step"] == "Analyzing chunks"
        assert status["total_scenes"] == 5
        assert status["active_job_id"] == "test_job_id"
    
    @pytest.mark.asyncio
    async def test_get_processing_status_no_active_job(self, orchestration_service):
        """Test getting status when no active job"""
        mock_video = AsyncMock(spec=Video)
        mock_video.id = "test_video_id"
        mock_video.status = VideoStatus.ANALYZED
        mock_video.total_scenes = 10
        
        with patch('models.Video.get', AsyncMock(return_value=mock_video)):
            with patch('models.ProcessingJob.find') as mock_find:
                mock_find.return_value.to_list = AsyncMock(return_value=[])
                
                status = await orchestration_service.get_processing_status("test_video_id")
        
        assert status["progress"] == 0
        assert status["current_step"] is None
        assert status["active_job_id"] is None