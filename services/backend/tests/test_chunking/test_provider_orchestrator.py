"""
Tests for ProviderOrchestrator - provider coordination, result merging
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from services.chunking.provider_orchestrator import ProviderOrchestrator
from services.analysis.base_analyzer import BaseAnalyzer
from schemas.analysis import (
    ChunkInfo, AnalysisConfig, AnalysisResult, ProviderType,
    SceneDetection, ObjectDetection, AnalysisGoal, VideoType
)
from models import ProcessingJob, Video, VideoStatus


class TestProviderOrchestrator:
    """Test suite for ProviderOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create ProviderOrchestrator instance"""
        with patch.object(ProviderOrchestrator, '_initialize_providers'):
            orchestrator = ProviderOrchestrator()
            orchestrator.providers = {}
            return orchestrator
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock analysis provider"""
        provider = Mock(spec=BaseAnalyzer)
        provider.analyze_chunk = AsyncMock()
        provider.estimate_cost = Mock(return_value=0.5)
        provider.get_capabilities = Mock(return_value={
            "name": "MockProvider",
            "capabilities": ["scene_detection"]
        })
        return provider
    
    @pytest.fixture
    def sample_chunk(self):
        """Create sample chunk info"""
        return ChunkInfo(
            chunk_id="chunk_0000",
            chunk_index=0,
            start_time=0.0,
            end_time=10.0,
            duration=10.0,
            s3_uri="s3://bucket/chunk.mp4",
            keyframe_path="s3://bucket/keyframe.jpg"
        )
    
    @pytest.fixture
    def sample_config(self):
        """Create sample analysis configuration"""
        return AnalysisConfig(
            user_prompt="Analyze scenes",
            video_type=VideoType.GENERAL,
            analysis_goals=[AnalysisGoal.SCENE_DETECTION],
            selected_providers={
                AnalysisGoal.SCENE_DETECTION.value: [ProviderType.AWS_REKOGNITION]
            },
            chunk_duration=10,
            chunk_overlap=2
        )
    
    @pytest.fixture
    def sample_video(self):
        """Create sample video document"""
        video = Mock(spec=Video)
        video.id = "test_video_id"
        video.filename = "test.mp4"
        video.duration = 120.0
        video.s3_uri = "s3://bucket/test.mp4"
        return video
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Create sample analysis result"""
        return AnalysisResult(
            video_id="test_video_id",
            chunk_id="chunk_0000",
            scenes=[
                SceneDetection(
                    scene_id="scene_001",
                    start_time=0.0,
                    end_time=5.0,
                    scene_type="action",
                    confidence=0.95,
                    description="Action scene"
                )
            ],
            objects=[
                ObjectDetection(
                    label="person",
                    confidence=0.98,
                    frame_time=2.5,
                    bounding_box={"x": 100, "y": 100, "width": 50, "height": 100}
                )
            ],
            captions=["Scene shows action"],
            custom_analysis={"emotion": "intense"},
            provider_metadata={
                "provider": "aws_rekognition",
                "api_calls": 1
            },
            processing_time=0.5,
            total_cost=0.1
        )
    
    def test_initialize_providers_all_fail(self):
        """Test provider initialization when all providers fail"""
        with patch('services.chunking.provider_orchestrator.NvidiaVilaAnalyzer', 
                  side_effect=Exception("No API key")):
            with patch('services.chunking.provider_orchestrator.AWSRekognitionAnalyzer',
                      side_effect=Exception("No credentials")):
                orchestrator = ProviderOrchestrator()
                assert len(orchestrator.providers) == 0
    
    def test_initialize_providers_partial_success(self):
        """Test provider initialization with partial success"""
        mock_nvidia = Mock()
        with patch('services.chunking.provider_orchestrator.NvidiaVilaAnalyzer',
                  return_value=mock_nvidia):
            with patch('services.chunking.provider_orchestrator.AWSRekognitionAnalyzer',
                      side_effect=Exception("No AWS credentials")):
                orchestrator = ProviderOrchestrator()
                assert ProviderType.NVIDIA_VILA in orchestrator.providers
                assert ProviderType.AWS_REKOGNITION not in orchestrator.providers
    
    @pytest.mark.asyncio
    async def test_analyze_chunk_with_providers_success(self, orchestrator, mock_provider,
                                                       sample_chunk, sample_config,
                                                       sample_analysis_result):
        """Test successful chunk analysis with providers"""
        orchestrator.providers[ProviderType.AWS_REKOGNITION] = mock_provider
        mock_provider.analyze_chunk.return_value = sample_analysis_result
        
        results = await orchestrator._analyze_chunk_with_providers(
            sample_chunk, sample_config, "test_video_id"
        )
        
        assert len(results) == 1
        assert results[0] == sample_analysis_result
        assert results[0].video_id == "test_video_id"
        mock_provider.analyze_chunk.assert_called_once_with(sample_chunk, sample_config)
    
    @pytest.mark.asyncio
    async def test_analyze_chunk_with_providers_not_available(self, orchestrator,
                                                             sample_chunk, sample_config):
        """Test chunk analysis when provider not available"""
        # No providers initialized
        results = await orchestrator._analyze_chunk_with_providers(
            sample_chunk, sample_config, "test_video_id"
        )
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_chunk_with_providers_error(self, orchestrator, mock_provider,
                                                      sample_chunk, sample_config):
        """Test chunk analysis when provider throws error"""
        orchestrator.providers[ProviderType.AWS_REKOGNITION] = mock_provider
        mock_provider.analyze_chunk.side_effect = Exception("API error")
        
        results = await orchestrator._analyze_chunk_with_providers(
            sample_chunk, sample_config, "test_video_id"
        )
        
        assert len(results) == 0  # Error results are filtered out
    
    @pytest.mark.asyncio
    async def test_analyze_chunk_multiple_providers(self, orchestrator, sample_chunk):
        """Test chunk analysis with multiple providers"""
        # Create multiple mock providers
        mock_aws = Mock(spec=BaseAnalyzer)
        mock_aws.analyze_chunk = AsyncMock(return_value=AnalysisResult(
            video_id="test", chunk_id="chunk_0000",
            provider_metadata={"provider": "aws"}
        ))
        
        mock_nvidia = Mock(spec=BaseAnalyzer)
        mock_nvidia.analyze_chunk = AsyncMock(return_value=AnalysisResult(
            video_id="test", chunk_id="chunk_0000",
            provider_metadata={"provider": "nvidia"}
        ))
        
        orchestrator.providers = {
            ProviderType.AWS_REKOGNITION: mock_aws,
            ProviderType.NVIDIA_VILA: mock_nvidia
        }
        
        config = AnalysisConfig(
            user_prompt="Test",
            selected_providers={
                AnalysisGoal.SCENE_DETECTION.value: [
                    ProviderType.AWS_REKOGNITION,
                    ProviderType.NVIDIA_VILA
                ]
            }
        )
        
        results = await orchestrator._analyze_chunk_with_providers(
            sample_chunk, config, "test_video_id"
        )
        
        assert len(results) == 2
        assert mock_aws.analyze_chunk.called
        assert mock_nvidia.analyze_chunk.called
    
    def test_merge_provider_results_empty(self, orchestrator, sample_chunk):
        """Test merging empty provider results"""
        merged = orchestrator._merge_provider_results([], sample_chunk, "test_video_id")
        
        assert merged.video_id == "test_video_id"
        assert merged.chunk_id == "chunk_0000"
        assert len(merged.scenes) == 0
        assert len(merged.objects) == 0
        assert merged.provider_metadata["error"] == "No provider results available"
    
    def test_merge_provider_results_single(self, orchestrator, sample_chunk,
                                          sample_analysis_result):
        """Test merging single provider result"""
        merged = orchestrator._merge_provider_results(
            [sample_analysis_result], sample_chunk, "test_video_id"
        )
        
        assert merged.video_id == "test_video_id"
        assert merged.chunk_id == "chunk_0000"
        assert len(merged.scenes) == 1
        assert len(merged.objects) == 1
        assert "aws_rekognition" in merged.provider_metadata["providers_used"]
        assert merged.total_cost == 0.1
    
    def test_merge_provider_results_multiple(self, orchestrator, sample_chunk):
        """Test merging multiple provider results"""
        result1 = AnalysisResult(
            video_id="test",
            chunk_id="chunk_0000",
            scenes=[SceneDetection(
                scene_id="scene_001",
                start_time=0.0,
                end_time=5.0,
                confidence=0.9
            )],
            objects=[ObjectDetection(
                label="person",
                confidence=0.95,
                frame_time=2.0
            )],
            custom_analysis={"key1": "value1"},
            provider_metadata={"provider": "aws"},
            total_cost=0.1,
            processing_time=0.5
        )
        
        result2 = AnalysisResult(
            video_id="test",
            chunk_id="chunk_0000",
            scenes=[
                SceneDetection(  # Duplicate scene (same times)
                    scene_id="scene_001_nvidia",
                    start_time=0.0,
                    end_time=5.0,
                    confidence=0.95
                ),
                SceneDetection(  # New scene
                    scene_id="scene_002",
                    start_time=5.0,
                    end_time=10.0,
                    confidence=0.85
                )
            ],
            objects=[
                ObjectDetection(  # Duplicate object (same label/time)
                    label="person",
                    confidence=0.98,  # Higher confidence
                    frame_time=2.0
                ),
                ObjectDetection(  # New object
                    label="car",
                    confidence=0.9,
                    frame_time=7.0
                )
            ],
            custom_analysis={"key1": "value2", "key2": "value3"},
            provider_metadata={"provider": "nvidia"},
            total_cost=0.2,
            processing_time=0.8
        )
        
        merged = orchestrator._merge_provider_results(
            [result1, result2], sample_chunk, "test_video_id"
        )
        
        # Check scenes - should have 2 (duplicate removed)
        assert len(merged.scenes) == 2
        assert merged.scenes[0].start_time == 0.0
        assert merged.scenes[1].start_time == 5.0
        
        # Check objects - should have 2 (duplicate removed, higher confidence kept)
        assert len(merged.objects) == 2
        person_obj = next(obj for obj in merged.objects if obj.label == "person")
        assert person_obj.confidence == 0.98  # Higher confidence kept
        
        # Check custom analysis - conflicting keys get provider prefix
        assert "key1" in merged.custom_analysis
        assert "nvidia_key1" in merged.custom_analysis
        assert merged.custom_analysis["key2"] == "value3"
        
        # Check metadata
        assert "aws" in merged.provider_metadata["providers_used"]
        assert "nvidia" in merged.provider_metadata["providers_used"]
        
        # Check costs and time
        assert merged.total_cost == 0.3  # Sum of costs
        assert merged.processing_time == 0.8  # Max time
    
    @pytest.mark.asyncio
    async def test_orchestrate_analysis_complete(self, orchestrator, mock_provider,
                                                sample_video, sample_config,
                                                sample_analysis_result):
        """Test complete orchestration flow"""
        orchestrator.providers[ProviderType.AWS_REKOGNITION] = mock_provider
        mock_provider.analyze_chunk.return_value = sample_analysis_result
        
        chunks = [
            ChunkInfo(
                chunk_id=f"chunk_{i:04d}",
                chunk_index=i,
                start_time=i * 10.0,
                end_time=(i + 1) * 10.0,
                duration=10.0,
                s3_uri=f"s3://bucket/chunk_{i}.mp4"
            )
            for i in range(3)
        ]
        
        mock_job = AsyncMock(spec=ProcessingJob)
        
        results = await orchestrator.orchestrate_analysis(
            chunks, sample_config, sample_video, mock_job
        )
        
        assert len(results) == 3
        assert mock_provider.analyze_chunk.call_count == 3
        assert mock_job.update_progress.call_count == 3
        
        # Verify progress updates
        progress_calls = mock_job.update_progress.call_args_list
        assert progress_calls[0][0][0] == 50  # First chunk
        assert "1/3" in progress_calls[0][0][1]
    
    @pytest.mark.asyncio
    async def test_orchestrate_analysis_no_job(self, orchestrator, mock_provider,
                                              sample_video, sample_config,
                                              sample_analysis_result):
        """Test orchestration without job tracking"""
        orchestrator.providers[ProviderType.AWS_REKOGNITION] = mock_provider
        mock_provider.analyze_chunk.return_value = sample_analysis_result
        
        chunks = [ChunkInfo(
            chunk_id="chunk_0000",
            chunk_index=0,
            start_time=0.0,
            end_time=10.0,
            duration=10.0
        )]
        
        results = await orchestrator.orchestrate_analysis(
            chunks, sample_config, sample_video, None
        )
        
        assert len(results) == 1
        assert mock_provider.analyze_chunk.called
    
    def test_get_available_providers(self, orchestrator, mock_provider):
        """Test getting available provider information"""
        orchestrator.providers = {
            ProviderType.AWS_REKOGNITION: mock_provider
        }
        
        available = orchestrator.get_available_providers()
        
        assert ProviderType.AWS_REKOGNITION.value in available
        assert available[ProviderType.AWS_REKOGNITION.value]["name"] == "MockProvider"
        mock_provider.get_capabilities.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_estimate_total_cost(self, orchestrator, mock_provider, sample_config):
        """Test total cost estimation"""
        orchestrator.providers = {
            ProviderType.AWS_REKOGNITION: mock_provider
        }
        mock_provider.estimate_cost.return_value = 0.5
        
        total_cost = await orchestrator.estimate_total_cost(120.0, sample_config)
        
        assert total_cost == 0.5
        mock_provider.estimate_cost.assert_called_once_with(120.0, sample_config)
    
    @pytest.mark.asyncio
    async def test_estimate_total_cost_multiple_providers(self, orchestrator):
        """Test cost estimation with multiple providers"""
        mock_aws = Mock(spec=BaseAnalyzer)
        mock_aws.estimate_cost = Mock(return_value=0.3)
        
        mock_nvidia = Mock(spec=BaseAnalyzer)
        mock_nvidia.estimate_cost = Mock(return_value=0.7)
        
        orchestrator.providers = {
            ProviderType.AWS_REKOGNITION: mock_aws,
            ProviderType.NVIDIA_VILA: mock_nvidia
        }
        
        config = AnalysisConfig(
            user_prompt="Test",
            selected_providers={
                AnalysisGoal.SCENE_DETECTION.value: [ProviderType.AWS_REKOGNITION],
                AnalysisGoal.ACTION_DETECTION.value: [ProviderType.NVIDIA_VILA]
            }
        )
        
        total_cost = await orchestrator.estimate_total_cost(120.0, config)
        
        assert total_cost == 1.0  # 0.3 + 0.7
        assert mock_aws.estimate_cost.called
        assert mock_nvidia.estimate_cost.called
    
    @pytest.mark.asyncio
    async def test_estimate_total_cost_provider_not_available(self, orchestrator):
        """Test cost estimation when provider not available"""
        config = AnalysisConfig(
            user_prompt="Test",
            selected_providers={
                AnalysisGoal.SCENE_DETECTION.value: [ProviderType.AWS_REKOGNITION]
            }
        )
        
        # No providers initialized
        total_cost = await orchestrator.estimate_total_cost(120.0, config)
        
        assert total_cost == 0.0