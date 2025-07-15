"""
Tests for AnalysisPlanner - goal detection, provider selection, cost estimation
"""
import pytest
from unittest.mock import Mock, patch
from typing import List

from services.chunking.analysis_planner import AnalysisPlanner
from schemas.analysis import (
    AnalysisConfig, AnalysisGoal, VideoType, ProviderType,
    ProviderCapability
)


class TestAnalysisPlanner:
    """Test suite for AnalysisPlanner"""
    
    @pytest.fixture
    def planner(self):
        """Create AnalysisPlanner instance"""
        return AnalysisPlanner()
    
    def test_detect_video_type_movie(self, planner):
        """Test movie type detection"""
        prompts = [
            "analyze this movie for action scenes",
            "find all characters in the film",
            "summarize the cinema plot"
        ]
        
        for prompt in prompts:
            video_type = planner._detect_video_type(prompt)
            assert video_type == VideoType.MOVIE
    
    def test_detect_video_type_sports(self, planner):
        """Test sports type detection"""
        prompts = [
            "analyze the basketball game highlights",
            "track players in the match",
            "find athletic moments"
        ]
        
        for prompt in prompts:
            video_type = planner._detect_video_type(prompt)
            assert video_type == VideoType.SPORTS
    
    def test_detect_video_type_default(self, planner):
        """Test default video type when no keywords match"""
        prompt = "analyze this video content"
        video_type = planner._detect_video_type(prompt)
        assert video_type == VideoType.GENERAL
    
    def test_extract_goals_action_detection(self, planner):
        """Test action detection goal extraction"""
        prompts = [
            "find all action scenes",
            "detect fight sequences",
            "identify chase moments",
            "find explosions and battles"
        ]
        
        for prompt in prompts:
            goals = planner._extract_goals(prompt)
            assert AnalysisGoal.ACTION_DETECTION in goals
    
    def test_extract_goals_scene_detection(self, planner):
        """Test scene detection goal extraction"""
        prompts = [
            "segment the video into scenes",
            "find scene transitions",
            "detect shot changes"
        ]
        
        for prompt in prompts:
            goals = planner._extract_goals(prompt)
            assert AnalysisGoal.SCENE_DETECTION in goals
    
    def test_extract_goals_character_tracking(self, planner):
        """Test character tracking goal extraction"""
        prompts = [
            "track all characters",
            "identify who appears when",
            "follow the protagonist"
        ]
        
        for prompt in prompts:
            goals = planner._extract_goals(prompt)
            assert AnalysisGoal.CHARACTER_TRACKING in goals
    
    def test_extract_goals_dialogue_extraction(self, planner):
        """Test dialogue extraction goal extraction"""
        prompts = [
            "extract all dialogue",
            "get the conversation transcript",
            "what do they say in the video"
        ]
        
        for prompt in prompts:
            goals = planner._extract_goals(prompt)
            assert AnalysisGoal.DIALOGUE_EXTRACTION in goals
    
    def test_extract_goals_comprehensive(self, planner):
        """Test comprehensive analysis keywords"""
        prompts = [
            "analyze everything in the video",
            "provide comprehensive analysis",
            "full analysis please"
        ]
        
        for prompt in prompts:
            goals = planner._extract_goals(prompt)
            assert AnalysisGoal.SCENE_DETECTION in goals
            assert AnalysisGoal.OBJECT_DETECTION in goals
            assert AnalysisGoal.PLOT_SUMMARY in goals
    
    def test_extract_goals_custom_query(self, planner):
        """Test custom query as default when no specific goals found"""
        prompt = "what is happening in this video"
        config = planner.analyze_prompt(prompt, 120.0)
        assert AnalysisGoal.CUSTOM_QUERY in config.analysis_goals
    
    def test_select_providers_action_detection(self, planner):
        """Test provider selection for action detection"""
        goals = [AnalysisGoal.ACTION_DETECTION]
        provider_map = planner._select_providers(goals, "find action scenes")
        
        assert AnalysisGoal.ACTION_DETECTION.value in provider_map
        assert ProviderType.NVIDIA_VILA in provider_map[AnalysisGoal.ACTION_DETECTION.value]
    
    def test_select_providers_scene_detection_simple(self, planner):
        """Test provider selection for simple scene detection"""
        goals = [AnalysisGoal.SCENE_DETECTION]
        provider_map = planner._select_providers(goals, "detect scenes")
        
        assert AnalysisGoal.SCENE_DETECTION.value in provider_map
        assert ProviderType.AWS_REKOGNITION in provider_map[AnalysisGoal.SCENE_DETECTION.value]
    
    def test_select_providers_scene_detection_complex(self, planner):
        """Test provider selection for complex scene detection"""
        goals = [AnalysisGoal.SCENE_DETECTION]
        provider_map = planner._select_providers(goals, "detailed scene analysis")
        
        assert AnalysisGoal.SCENE_DETECTION.value in provider_map
        assert ProviderType.NVIDIA_VILA in provider_map[AnalysisGoal.SCENE_DETECTION.value]
    
    def test_select_providers_dialogue_extraction(self, planner):
        """Test provider selection for dialogue extraction"""
        goals = [AnalysisGoal.DIALOGUE_EXTRACTION]
        provider_map = planner._select_providers(goals, "extract dialogue")
        
        assert AnalysisGoal.DIALOGUE_EXTRACTION.value in provider_map
        assert ProviderType.WHISPER in provider_map[AnalysisGoal.DIALOGUE_EXTRACTION.value]
    
    def test_select_providers_custom_query(self, planner):
        """Test provider selection for custom queries"""
        goals = [AnalysisGoal.CUSTOM_QUERY]
        provider_map = planner._select_providers(goals, "analyze this video")
        
        assert AnalysisGoal.CUSTOM_QUERY.value in provider_map
        providers = provider_map[AnalysisGoal.CUSTOM_QUERY.value]
        assert ProviderType.NVIDIA_VILA in providers or ProviderType.OPENAI_GPT4V in providers
    
    def test_determine_chunk_settings_movie(self, planner):
        """Test chunk settings for movies"""
        chunk_duration, overlap = planner._determine_chunk_settings(
            VideoType.MOVIE, 
            [AnalysisGoal.SCENE_DETECTION],
            3600.0  # 1 hour
        )
        
        assert chunk_duration == 30
        assert overlap == 5
    
    def test_determine_chunk_settings_sports(self, planner):
        """Test chunk settings for sports videos"""
        chunk_duration, overlap = planner._determine_chunk_settings(
            VideoType.SPORTS,
            [AnalysisGoal.ACTION_DETECTION],
            1800.0  # 30 minutes
        )
        
        assert chunk_duration == 10
        assert overlap == 3
    
    def test_determine_chunk_settings_surveillance(self, planner):
        """Test chunk settings for surveillance videos"""
        chunk_duration, overlap = planner._determine_chunk_settings(
            VideoType.SURVEILLANCE,
            [AnalysisGoal.OBJECT_DETECTION],
            7200.0  # 2 hours
        )
        
        assert chunk_duration == 60
        assert overlap == 10
    
    def test_determine_chunk_settings_short_video(self, planner):
        """Test chunk settings for very short videos"""
        chunk_duration, overlap = planner._determine_chunk_settings(
            VideoType.GENERAL,
            [AnalysisGoal.SCENE_DETECTION],
            45.0  # 45 seconds
        )
        
        assert chunk_duration <= 15  # Should be limited for short videos
        assert overlap == 1
    
    def test_determine_chunk_settings_action_adjustment(self, planner):
        """Test chunk settings adjustment for action detection"""
        chunk_duration, overlap = planner._determine_chunk_settings(
            VideoType.MOVIE,
            [AnalysisGoal.ACTION_DETECTION],
            3600.0
        )
        
        assert chunk_duration <= 15  # Should be shorter for action
        assert overlap >= 3
    
    def test_create_custom_prompts(self, planner):
        """Test custom prompt creation for providers"""
        user_prompt = "find all action scenes and describe them"
        goals = [AnalysisGoal.ACTION_DETECTION]
        provider_map = {
            AnalysisGoal.ACTION_DETECTION.value: [ProviderType.NVIDIA_VILA]
        }
        
        custom_prompts = planner._create_custom_prompts(
            user_prompt, goals, provider_map
        )
        
        assert ProviderType.NVIDIA_VILA.value in custom_prompts
        assert "action_detection" in custom_prompts[ProviderType.NVIDIA_VILA.value]
        assert user_prompt in custom_prompts[ProviderType.NVIDIA_VILA.value]
    
    def test_create_custom_prompts_multiple_providers(self, planner):
        """Test custom prompt creation for multiple providers"""
        user_prompt = "analyze the emotional content"
        goals = [AnalysisGoal.EMOTION_ANALYSIS, AnalysisGoal.CUSTOM_QUERY]
        provider_map = {
            AnalysisGoal.EMOTION_ANALYSIS.value: [ProviderType.OPENAI_GPT4V],
            AnalysisGoal.CUSTOM_QUERY.value: [ProviderType.NVIDIA_VILA]
        }
        
        custom_prompts = planner._create_custom_prompts(
            user_prompt, goals, provider_map
        )
        
        assert ProviderType.NVIDIA_VILA.value in custom_prompts
        assert ProviderType.OPENAI_GPT4V.value in custom_prompts
    
    def test_estimate_cost_single_provider(self, planner):
        """Test cost estimation for single provider"""
        provider_map = {
            AnalysisGoal.SCENE_DETECTION.value: [ProviderType.AWS_REKOGNITION]
        }
        
        cost = planner._estimate_cost(provider_map, 600.0, 30)  # 10 minutes
        
        # AWS costs $0.001 per frame
        # 20 chunks (600s / 30s), 10 frames per chunk = 200 frames
        # 200 * 0.001 = $0.20
        assert cost == 0.20
    
    def test_estimate_cost_whisper(self, planner):
        """Test cost estimation for Whisper (audio processing)"""
        provider_map = {
            AnalysisGoal.DIALOGUE_EXTRACTION.value: [ProviderType.WHISPER]
        }
        
        cost = planner._estimate_cost(provider_map, 600.0, 30)  # 10 minutes
        
        # Whisper costs $0.006 per minute
        # 10 minutes * 0.006 = $0.06
        assert cost == 0.06
    
    def test_estimate_cost_multiple_providers(self, planner):
        """Test cost estimation for multiple providers"""
        provider_map = {
            AnalysisGoal.SCENE_DETECTION.value: [ProviderType.AWS_REKOGNITION],
            AnalysisGoal.ACTION_DETECTION.value: [ProviderType.NVIDIA_VILA],
            AnalysisGoal.DIALOGUE_EXTRACTION.value: [ProviderType.WHISPER]
        }
        
        cost = planner._estimate_cost(provider_map, 600.0, 30)  # 10 minutes
        
        # AWS: 200 frames * $0.001 = $0.20
        # NVIDIA: 200 frames * $0.0035 = $0.70
        # Whisper: 10 minutes * $0.006 = $0.06
        # Total: $0.96
        assert cost == 0.96
    
    def test_analyze_prompt_complete_flow(self, planner):
        """Test complete analysis prompt flow"""
        prompt = "Find all action scenes and track characters in this movie"
        duration = 3600.0  # 1 hour
        
        config = planner.analyze_prompt(prompt, duration)
        
        # Check basic config
        assert config.user_prompt == prompt
        assert config.video_type == VideoType.MOVIE
        
        # Check goals
        assert AnalysisGoal.ACTION_DETECTION in config.analysis_goals
        assert AnalysisGoal.CHARACTER_TRACKING in config.analysis_goals
        
        # Check providers
        assert AnalysisGoal.ACTION_DETECTION.value in config.selected_providers
        assert AnalysisGoal.CHARACTER_TRACKING.value in config.selected_providers
        
        # Check chunk settings
        assert config.chunk_duration > 0
        assert config.chunk_overlap >= 0
        assert config.chunk_overlap < config.chunk_duration
        
        # Check cost estimate
        assert config.cost_estimate > 0
        
        # Check custom prompts
        assert len(config.custom_prompts) > 0
    
    def test_analyze_prompt_no_specific_goals(self, planner):
        """Test analysis when no specific goals are detected"""
        prompt = "What's in this video?"
        duration = 120.0
        
        config = planner.analyze_prompt(prompt, duration)
        
        # Should default to custom query
        assert AnalysisGoal.CUSTOM_QUERY in config.analysis_goals
        assert len(config.selected_providers) > 0
    
    def test_get_provider_info(self, planner):
        """Test getting provider capability information"""
        info = planner.get_provider_info(ProviderType.AWS_REKOGNITION)
        
        assert info is not None
        assert info.provider == ProviderType.AWS_REKOGNITION
        assert AnalysisGoal.SCENE_DETECTION in info.capabilities
        assert info.cost_per_frame == 0.001
        assert info.supports_custom_prompts == False
    
    def test_get_provider_info_invalid(self, planner):
        """Test getting info for non-existent provider"""
        info = planner.get_provider_info(ProviderType.CUSTOM)
        assert info is None