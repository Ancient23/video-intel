"""
NVIDIA VILA Vision-Language Model Provider
"""
import os
import time
import base64
from typing import List, Dict, Any, Optional
import httpx
import structlog
from pathlib import Path

from ..base_analyzer import BaseAnalyzer
from ....schemas.analysis import (
    ChunkInfo, AnalysisConfig, AnalysisResult, AnalysisGoal,
    SceneDetection, ObjectDetection, ProviderType
)

logger = structlog.get_logger()


class NvidiaVilaAnalyzer(BaseAnalyzer):
    """NVIDIA VILA model for scene understanding and action detection"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("NVIDIA_API_KEY"))
        self.provider_type = ProviderType.NVIDIA_VILA
        self.base_url = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions"
        self.model_id = "nvidia/vila"  # Update with actual model ID
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def analyze_chunk(
        self,
        chunk: ChunkInfo,
        config: AnalysisConfig
    ) -> AnalysisResult:
        """Analyze video chunk using NVIDIA VILA"""
        start_time = time.time()
        
        if not self.validate_chunk(chunk):
            return self.handle_error(ValueError("Invalid chunk"), chunk)
        
        try:
            # Extract frames from chunk
            frames = await self._extract_frames(chunk, config.max_frames_per_chunk)
            
            # Get custom prompt or use default
            prompt = config.custom_prompts.get(
                self.provider_type.value,
                self._create_default_prompt(config)
            )
            
            # Analyze frames with VILA
            response = await self._call_vila_api(frames, prompt)
            
            # Parse response into structured results
            result = self._parse_response(response, chunk, config)
            
            # Add processing time
            result.processing_time = time.time() - start_time
            
            # Calculate cost
            result.total_cost = len(frames) * 0.0035  # $0.0035 per frame
            
            return result
            
        except Exception as e:
            return self.handle_error(e, chunk)
    
    async def _extract_frames(
        self,
        chunk: ChunkInfo,
        max_frames: int
    ) -> List[str]:
        """Extract frames from video chunk"""
        frames = []
        
        # Use local path if available, otherwise download from S3
        video_path = chunk.local_path
        if not video_path and chunk.s3_uri:
            # TODO: Download from S3 to temp file
            raise NotImplementedError("S3 download not implemented yet")
        
        # Extract frames using ffmpeg
        import ffmpeg
        
        # Calculate frame interval
        fps = 30  # Assume 30 fps, should get from video info
        total_frames = int(chunk.duration * fps)
        interval = max(1, total_frames // max_frames)
        
        try:
            # Extract frames at intervals
            for i in range(0, min(max_frames, total_frames), interval):
                frame_time = i / fps
                
                # Extract single frame
                out, _ = (
                    ffmpeg
                    .input(video_path, ss=frame_time)
                    .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
                    .run(capture_stdout=True, quiet=True)
                )
                
                # Convert to base64
                frame_b64 = base64.b64encode(out).decode('utf-8')
                frames.append(frame_b64)
                
        except Exception as e:
            logger.error("Frame extraction failed", error=str(e))
            raise
        
        logger.info(f"Extracted {len(frames)} frames from chunk {chunk.chunk_id}")
        return frames
    
    async def _call_vila_api(
        self,
        frames: List[str],
        prompt: str
    ) -> Dict[str, Any]:
        """Call NVIDIA VILA API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare request
        payload = {
            "model": self.model_id,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ] + [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}}
                    for frame in frames
                ]
            }],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/{self.model_id}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error("NVIDIA API call failed", error=str(e))
            raise
    
    def _create_default_prompt(self, config: AnalysisConfig) -> str:
        """Create default prompt based on analysis goals"""
        goal_prompts = {
            AnalysisGoal.SCENE_DETECTION: "Identify scene changes and describe each scene.",
            AnalysisGoal.ACTION_DETECTION: "Identify and describe any action sequences, movements, or dynamic events.",
            AnalysisGoal.PLOT_SUMMARY: "Summarize what happens in this video segment.",
            AnalysisGoal.CUSTOM_QUERY: "Analyze this video segment and provide detailed observations."
        }
        
        prompts = []
        for goal in config.analysis_goals:
            if goal in goal_prompts:
                prompts.append(goal_prompts[goal])
        
        base_prompt = "Analyze this video segment. " + " ".join(prompts)
        base_prompt += " For each observation, provide approximate timestamps."
        
        return base_prompt
    
    def _parse_response(
        self,
        response: Dict[str, Any],
        chunk: ChunkInfo,
        config: AnalysisConfig
    ) -> AnalysisResult:
        """Parse VILA API response into structured results"""
        result = self.create_result("", chunk)
        
        # Extract text from response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse scenes if scene detection was requested
        if AnalysisGoal.SCENE_DETECTION in config.analysis_goals:
            scenes = self._extract_scenes(content, chunk)
            result.scenes = scenes
        
        # Parse action sequences
        if AnalysisGoal.ACTION_DETECTION in config.analysis_goals:
            # Store in custom analysis for now
            result.custom_analysis["action_sequences"] = self._extract_actions(content)
        
        # Store raw response
        result.custom_analysis["vila_response"] = content
        
        # Add provider metadata
        result.provider_metadata.update({
            "model": self.model_id,
            "frames_analyzed": len(result.provider_metadata.get("frames", [])),
            "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": response.get("usage", {}).get("completion_tokens", 0)
        })
        
        return result
    
    def _extract_scenes(self, content: str, chunk: ChunkInfo) -> List[SceneDetection]:
        """Extract scene information from text response"""
        scenes = []
        
        # Simple parsing - in production, use more sophisticated NLP
        lines = content.split('\n')
        scene_count = 0
        
        for line in lines:
            if 'scene' in line.lower() or 'shot' in line.lower():
                # Create scene detection
                scene = SceneDetection(
                    scene_id=f"{chunk.chunk_id}_scene_{scene_count}",
                    start_time=chunk.start_time,  # Approximate
                    end_time=chunk.end_time,      # Approximate
                    description=line.strip(),
                    confidence=0.8,  # VILA doesn't provide confidence
                    provider=self.provider_type
                )
                scenes.append(scene)
                scene_count += 1
        
        return scenes
    
    def _extract_actions(self, content: str) -> List[Dict[str, Any]]:
        """Extract action sequences from text response"""
        actions = []
        
        # Look for action-related keywords
        action_keywords = ['action', 'movement', 'fight', 'chase', 'run', 'jump']
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in action_keywords):
                actions.append({
                    "description": line.strip(),
                    "type": "action",
                    "confidence": 0.7
                })
        
        return actions
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get NVIDIA VILA capabilities"""
        return {
            "provider": self.provider_type.value,
            "supported_goals": [
                AnalysisGoal.SCENE_DETECTION.value,
                AnalysisGoal.ACTION_DETECTION.value,
                AnalysisGoal.PLOT_SUMMARY.value,
                AnalysisGoal.CUSTOM_QUERY.value
            ],
            "max_frames_per_request": 50,
            "supports_custom_prompts": True,
            "cost_per_frame": 0.0035,
            "models": ["vila-v1.5"]
        }
    
    def estimate_cost(
        self,
        duration_seconds: float,
        config: AnalysisConfig
    ) -> float:
        """Estimate cost for NVIDIA VILA analysis"""
        # Estimate frames based on chunk settings
        num_chunks = max(1, int(duration_seconds / config.chunk_duration))
        frames_per_chunk = min(config.max_frames_per_chunk, 30)
        total_frames = num_chunks * frames_per_chunk
        
        return total_frames * 0.0035
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()