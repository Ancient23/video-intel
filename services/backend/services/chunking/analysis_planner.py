"""
Analysis Planner - Interprets user prompts and selects appropriate providers
"""
import re
from typing import List, Dict, Set, Tuple
from ...schemas.analysis import (
    AnalysisConfig, AnalysisGoal, VideoType, ProviderType,
    ProviderCapability
)
import structlog

logger = structlog.get_logger()


class AnalysisPlanner:
    """Plans video analysis based on user prompts"""
    
    # Provider capabilities and costs
    PROVIDER_CAPABILITIES = {
        ProviderType.AWS_REKOGNITION: ProviderCapability(
            provider=ProviderType.AWS_REKOGNITION,
            capabilities=[
                AnalysisGoal.SCENE_DETECTION,
                AnalysisGoal.OBJECT_DETECTION,
                AnalysisGoal.CHARACTER_TRACKING,
                AnalysisGoal.TECHNICAL_ANALYSIS
            ],
            cost_per_frame=0.001,
            cost_per_minute=1.0,
            supports_custom_prompts=False,
            max_frames_per_request=100
        ),
        ProviderType.NVIDIA_VILA: ProviderCapability(
            provider=ProviderType.NVIDIA_VILA,
            capabilities=[
                AnalysisGoal.SCENE_DETECTION,
                AnalysisGoal.ACTION_DETECTION,
                AnalysisGoal.PLOT_SUMMARY,
                AnalysisGoal.CUSTOM_QUERY
            ],
            cost_per_frame=0.0035,
            cost_per_minute=3.5,
            supports_custom_prompts=True,
            max_frames_per_request=50
        ),
        ProviderType.NVIDIA_COSMOS: ProviderCapability(
            provider=ProviderType.NVIDIA_COSMOS,
            capabilities=[
                AnalysisGoal.OBJECT_DETECTION,
                AnalysisGoal.CHARACTER_TRACKING,
                AnalysisGoal.ACTION_DETECTION,
                AnalysisGoal.CUSTOM_QUERY
            ],
            cost_per_frame=0.0035,
            cost_per_minute=3.5,
            supports_custom_prompts=True,
            max_frames_per_request=50
        ),
        ProviderType.OPENAI_GPT4V: ProviderCapability(
            provider=ProviderType.OPENAI_GPT4V,
            capabilities=[
                AnalysisGoal.SCENE_DETECTION,
                AnalysisGoal.EMOTION_ANALYSIS,
                AnalysisGoal.PLOT_SUMMARY,
                AnalysisGoal.CUSTOM_QUERY
            ],
            cost_per_frame=0.003,
            cost_per_minute=3.0,
            supports_custom_prompts=True,
            max_frames_per_request=20
        ),
        ProviderType.WHISPER: ProviderCapability(
            provider=ProviderType.WHISPER,
            capabilities=[
                AnalysisGoal.DIALOGUE_EXTRACTION
            ],
            cost_per_frame=0.0,
            cost_per_minute=0.006,
            supports_custom_prompts=False,
            max_frames_per_request=0  # Audio only
        )
    }
    
    # Keywords mapping to analysis goals
    GOAL_KEYWORDS = {
        AnalysisGoal.ACTION_DETECTION: [
            "action", "fight", "chase", "explosion", "movement", "dynamic",
            "combat", "battle", "conflict", "intense"
        ],
        AnalysisGoal.SCENE_DETECTION: [
            "scene", "segment", "section", "part", "sequence", "shot",
            "transition", "cut", "change"
        ],
        AnalysisGoal.CHARACTER_TRACKING: [
            "character", "person", "people", "actor", "protagonist",
            "track", "follow", "identify", "who"
        ],
        AnalysisGoal.OBJECT_DETECTION: [
            "object", "item", "thing", "detect", "find", "locate",
            "what", "identify objects"
        ],
        AnalysisGoal.DIALOGUE_EXTRACTION: [
            "dialogue", "conversation", "speech", "talking", "words",
            "transcript", "subtitle", "what they say"
        ],
        AnalysisGoal.EMOTION_ANALYSIS: [
            "emotion", "feeling", "mood", "sentiment", "expression",
            "happy", "sad", "angry", "reaction"
        ],
        AnalysisGoal.PLOT_SUMMARY: [
            "plot", "story", "summary", "summarize", "narrative",
            "what happens", "storyline", "synopsis"
        ],
        AnalysisGoal.TECHNICAL_ANALYSIS: [
            "technical", "quality", "resolution", "fps", "codec",
            "format", "encoding", "technical details"
        ]
    }
    
    # Video type keywords
    VIDEO_TYPE_KEYWORDS = {
        VideoType.MOVIE: ["movie", "film", "cinema", "feature"],
        VideoType.DOCUMENTARY: ["documentary", "docu", "educational"],
        VideoType.TUTORIAL: ["tutorial", "how-to", "instruction", "guide"],
        VideoType.SPORTS: ["sports", "game", "match", "athletic"],
        VideoType.NEWS: ["news", "broadcast", "report"],
        VideoType.SURVEILLANCE: ["surveillance", "security", "cctv", "monitor"]
    }
    
    def analyze_prompt(self, prompt: str, video_duration_seconds: float) -> AnalysisConfig:
        """
        Analyze user prompt and create analysis configuration
        
        Args:
            prompt: User's analysis request
            video_duration_seconds: Duration of the video
            
        Returns:
            AnalysisConfig with selected providers and settings
        """
        prompt_lower = prompt.lower()
        
        # Detect video type
        video_type = self._detect_video_type(prompt_lower)
        
        # Extract analysis goals
        goals = self._extract_goals(prompt_lower)
        
        # If no specific goals found, add custom query
        if not goals:
            goals = [AnalysisGoal.CUSTOM_QUERY]
        
        # Select providers based on goals
        provider_map = self._select_providers(goals, prompt_lower)
        
        # Determine chunk settings based on content
        chunk_duration, chunk_overlap = self._determine_chunk_settings(
            video_type, goals, video_duration_seconds
        )
        
        # Create custom prompts for providers that support them
        custom_prompts = self._create_custom_prompts(prompt, goals, provider_map)
        
        # Estimate cost
        cost_estimate = self._estimate_cost(
            provider_map, video_duration_seconds, chunk_duration
        )
        
        config = AnalysisConfig(
            user_prompt=prompt,
            video_type=video_type,
            analysis_goals=goals,
            selected_providers=provider_map,
            chunk_duration=chunk_duration,
            chunk_overlap=chunk_overlap,
            cost_estimate=cost_estimate,
            custom_prompts=custom_prompts
        )
        
        logger.info(
            "Analysis plan created",
            goals=goals,
            providers=list(set(p for providers in provider_map.values() for p in providers)),
            cost_estimate=cost_estimate
        )
        
        return config
    
    def _detect_video_type(self, prompt: str) -> VideoType:
        """Detect video type from prompt"""
        for video_type, keywords in self.VIDEO_TYPE_KEYWORDS.items():
            if any(keyword in prompt for keyword in keywords):
                return video_type
        return VideoType.GENERAL
    
    def _extract_goals(self, prompt: str) -> List[AnalysisGoal]:
        """Extract analysis goals from prompt"""
        goals = set()
        
        for goal, keywords in self.GOAL_KEYWORDS.items():
            if any(keyword in prompt for keyword in keywords):
                goals.add(goal)
        
        # Special cases
        if "everything" in prompt or "comprehensive" in prompt or "full analysis" in prompt:
            goals.update([
                AnalysisGoal.SCENE_DETECTION,
                AnalysisGoal.OBJECT_DETECTION,
                AnalysisGoal.PLOT_SUMMARY
            ])
        
        return list(goals)
    
    def _select_providers(
        self, 
        goals: List[AnalysisGoal], 
        prompt: str
    ) -> Dict[str, List[ProviderType]]:
        """Select optimal providers for each goal"""
        provider_map = {}
        
        for goal in goals:
            providers = []
            
            # Find providers that support this goal
            capable_providers = [
                cap.provider for cap in self.PROVIDER_CAPABILITIES.values()
                if goal in cap.capabilities
            ]
            
            # Apply selection logic
            if goal == AnalysisGoal.ACTION_DETECTION:
                # NVIDIA is best for action
                providers = [ProviderType.NVIDIA_VILA]
            elif goal == AnalysisGoal.SCENE_DETECTION:
                # Use AWS for basic, NVIDIA for complex
                if "detailed" in prompt or "complex" in prompt:
                    providers = [ProviderType.NVIDIA_VILA]
                else:
                    providers = [ProviderType.AWS_REKOGNITION]
            elif goal == AnalysisGoal.DIALOGUE_EXTRACTION:
                providers = [ProviderType.WHISPER]
            elif goal == AnalysisGoal.CUSTOM_QUERY:
                # Prefer providers that support custom prompts
                providers = [ProviderType.NVIDIA_VILA, ProviderType.OPENAI_GPT4V]
            else:
                # Use most cost-effective provider
                providers = [capable_providers[0]] if capable_providers else []
            
            if providers:
                provider_map[goal.value] = providers
        
        return provider_map
    
    def _determine_chunk_settings(
        self, 
        video_type: VideoType,
        goals: List[AnalysisGoal],
        video_duration: float
    ) -> Tuple[int, int]:
        """Determine optimal chunk duration and overlap"""
        # Base settings
        chunk_duration = 10
        chunk_overlap = 2
        
        # Adjust based on video type
        if video_type == VideoType.MOVIE:
            chunk_duration = 30  # Longer scenes
            chunk_overlap = 5
        elif video_type == VideoType.SPORTS:
            chunk_duration = 10  # Fast action
            chunk_overlap = 3
        elif video_type == VideoType.SURVEILLANCE:
            chunk_duration = 60  # Long static shots
            chunk_overlap = 10
        
        # Adjust based on goals
        if AnalysisGoal.ACTION_DETECTION in goals:
            chunk_duration = min(chunk_duration, 15)  # Shorter for action
            chunk_overlap = max(chunk_overlap, 3)
        
        # Limit based on video duration
        if video_duration < 60:  # Less than 1 minute
            chunk_duration = min(chunk_duration, int(video_duration / 3))
            chunk_overlap = min(chunk_overlap, 1)
        
        return chunk_duration, chunk_overlap
    
    def _create_custom_prompts(
        self,
        user_prompt: str,
        goals: List[AnalysisGoal],
        provider_map: Dict[str, List[ProviderType]]
    ) -> Dict[str, str]:
        """Create custom prompts for providers that support them"""
        custom_prompts = {}
        
        # Get all providers that support custom prompts
        custom_providers = set()
        for providers in provider_map.values():
            for provider in providers:
                if self.PROVIDER_CAPABILITIES[provider].supports_custom_prompts:
                    custom_providers.add(provider)
        
        # Create prompts for each provider
        for provider in custom_providers:
            if provider == ProviderType.NVIDIA_VILA:
                custom_prompts[provider.value] = (
                    f"Analyze this video segment and {user_prompt}. "
                    f"Focus on: {', '.join(g.value for g in goals)}. "
                    f"Provide detailed descriptions and timestamps."
                )
            elif provider == ProviderType.OPENAI_GPT4V:
                custom_prompts[provider.value] = (
                    f"You are analyzing a video segment. {user_prompt} "
                    f"Provide structured analysis including scene descriptions, "
                    f"notable events, and relevant details."
                )
        
        return custom_prompts
    
    def _estimate_cost(
        self,
        provider_map: Dict[str, List[ProviderType]],
        video_duration_seconds: float,
        chunk_duration: int
    ) -> float:
        """Estimate total cost of analysis"""
        total_cost = 0.0
        video_duration_minutes = video_duration_seconds / 60
        
        # Get unique providers
        all_providers = set()
        for providers in provider_map.values():
            all_providers.update(providers)
        
        # Calculate cost for each provider
        for provider in all_providers:
            capability = self.PROVIDER_CAPABILITIES[provider]
            
            if provider == ProviderType.WHISPER:
                # Audio processing cost
                total_cost += capability.cost_per_minute * video_duration_minutes
            else:
                # Frame processing cost
                # Estimate frames based on chunk settings
                num_chunks = max(1, int(video_duration_seconds / chunk_duration))
                frames_per_chunk = 10  # Conservative estimate
                total_frames = num_chunks * frames_per_chunk
                
                total_cost += capability.cost_per_frame * total_frames
        
        return round(total_cost, 2)
    
    def get_provider_info(self, provider: ProviderType) -> ProviderCapability:
        """Get capability information for a provider"""
        return self.PROVIDER_CAPABILITIES.get(provider)