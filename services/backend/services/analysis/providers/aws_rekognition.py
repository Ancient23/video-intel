"""
AWS Rekognition Provider for video analysis
"""
import os
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

from ..base_analyzer import BaseAnalyzer
from ....schemas.analysis import (
    ChunkInfo, AnalysisConfig, AnalysisResult, AnalysisGoal,
    SceneDetection, ObjectDetection, ProviderType
)

logger = structlog.get_logger()


class AWSRekognitionAnalyzer(BaseAnalyzer):
    """AWS Rekognition for shot detection and object tracking"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.provider_type = ProviderType.AWS_REKOGNITION
        self.client = boto3.client('rekognition')
        self.s3_client = boto3.client('s3')
        
    async def analyze_chunk(
        self,
        chunk: ChunkInfo,
        config: AnalysisConfig
    ) -> AnalysisResult:
        """Analyze video chunk using AWS Rekognition"""
        start_time = time.time()
        
        if not self.validate_chunk(chunk):
            return self.handle_error(ValueError("Invalid chunk"), chunk)
        
        try:
            # Ensure chunk is in S3 (Rekognition requires S3)
            if not chunk.s3_uri:
                raise ValueError("AWS Rekognition requires video to be in S3")
            
            bucket, key = self._parse_s3_uri(chunk.s3_uri)
            
            result = self.create_result("", chunk)
            
            # Run different analyses based on goals
            if AnalysisGoal.SCENE_DETECTION in config.analysis_goals:
                scenes = await self._detect_shots(bucket, key, chunk)
                result.scenes = scenes
            
            if AnalysisGoal.OBJECT_DETECTION in config.analysis_goals:
                objects = await self._detect_objects(bucket, key, chunk)
                result.objects = objects
            
            if AnalysisGoal.TECHNICAL_ANALYSIS in config.analysis_goals:
                tech_info = await self._get_technical_info(bucket, key)
                result.custom_analysis["technical_info"] = tech_info
            
            # Calculate processing time and cost
            result.processing_time = time.time() - start_time
            result.total_cost = chunk.duration * 0.001  # $0.001 per second
            
            return result
            
        except Exception as e:
            return self.handle_error(e, chunk)
    
    def _parse_s3_uri(self, s3_uri: str) -> tuple:
        """Parse S3 URI into bucket and key"""
        parts = s3_uri[5:].split('/', 1)
        return parts[0], parts[1]
    
    async def _detect_shots(
        self,
        bucket: str,
        key: str,
        chunk: ChunkInfo
    ) -> List[SceneDetection]:
        """Detect shot boundaries using Rekognition"""
        try:
            # Start shot detection job
            response = self.client.start_shot_detection(
                Video={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                NotificationChannel={
                    'RoleArn': os.getenv('AWS_REKOGNITION_ROLE_ARN', ''),
                    'SNSTopicArn': os.getenv('AWS_REKOGNITION_SNS_TOPIC', '')
                } if os.getenv('AWS_REKOGNITION_ROLE_ARN') else {}
            )
            
            job_id = response['JobId']
            
            # Wait for job completion (polling)
            shots = await self._wait_for_job_completion(
                job_id,
                'get_shot_detection'
            )
            
            # Convert to our schema
            scenes = []
            for i, shot in enumerate(shots):
                # Adjust timestamps relative to chunk
                start = chunk.start_time + (shot['StartTimestampMillis'] / 1000)
                end = chunk.start_time + (shot['EndTimestampMillis'] / 1000)
                
                scene = SceneDetection(
                    scene_id=f"{chunk.chunk_id}_shot_{i}",
                    start_time=start,
                    end_time=end,
                    scene_type=shot.get('Type', 'SHOT'),
                    confidence=shot.get('Confidence', 0) / 100,
                    provider=self.provider_type
                )
                scenes.append(scene)
            
            return scenes
            
        except ClientError as e:
            logger.error("Shot detection failed", error=str(e))
            return []
    
    async def _detect_objects(
        self,
        bucket: str,
        key: str,
        chunk: ChunkInfo
    ) -> List[ObjectDetection]:
        """Detect and track objects in video"""
        try:
            # Start label detection job
            response = self.client.start_label_detection(
                Video={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                MinConfidence=70
            )
            
            job_id = response['JobId']
            
            # Wait for job completion
            labels = await self._wait_for_job_completion(
                job_id,
                'get_label_detection'
            )
            
            # Convert to our schema
            objects = []
            for label_detection in labels:
                label = label_detection['Label']
                timestamp = label_detection['Timestamp'] / 1000  # Convert to seconds
                
                # Create object for each instance
                for instance in label.get('Instances', []):
                    obj = ObjectDetection(
                        object_id=f"{chunk.chunk_id}_{label['Name']}_{timestamp}",
                        label=label['Name'],
                        confidence=label['Confidence'] / 100,
                        bounding_box=instance.get('BoundingBox'),
                        frame_time=chunk.start_time + timestamp,
                        provider=self.provider_type
                    )
                    objects.append(obj)
            
            return objects
            
        except ClientError as e:
            logger.error("Object detection failed", error=str(e))
            return []
    
    async def _get_technical_info(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """Get technical video information"""
        try:
            response = self.client.start_technical_cue_detection(
                Video={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            job_id = response['JobId']
            segments = await self._wait_for_job_completion(
                job_id,
                'get_technical_cue_detection'
            )
            
            return {
                "segments": segments,
                "total_segments": len(segments)
            }
            
        except ClientError as e:
            logger.error("Technical analysis failed", error=str(e))
            return {}
    
    async def _wait_for_job_completion(
        self,
        job_id: str,
        get_method: str,
        max_attempts: int = 60
    ) -> List[Dict[str, Any]]:
        """Wait for Rekognition job to complete"""
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Get job status
                if get_method == 'get_shot_detection':
                    response = self.client.get_shot_detection(JobId=job_id)
                elif get_method == 'get_label_detection':
                    response = self.client.get_label_detection(JobId=job_id)
                elif get_method == 'get_technical_cue_detection':
                    response = self.client.get_technical_cue_detection(JobId=job_id)
                else:
                    raise ValueError(f"Unknown method: {get_method}")
                
                status = response['JobStatus']
                
                if status == 'SUCCEEDED':
                    # Get all results with pagination
                    results = []
                    next_token = None
                    
                    while True:
                        if next_token:
                            response = getattr(self.client, get_method)(
                                JobId=job_id,
                                NextToken=next_token
                            )
                        
                        # Extract results based on method
                        if 'Shots' in response:
                            results.extend(response['Shots'])
                        elif 'Labels' in response:
                            results.extend(response['Labels'])
                        elif 'Segments' in response:
                            results.extend(response['Segments'])
                        
                        next_token = response.get('NextToken')
                        if not next_token:
                            break
                    
                    return results
                    
                elif status == 'FAILED':
                    raise Exception(f"Rekognition job failed: {response.get('StatusMessage')}")
                
                # Still in progress
                await asyncio.sleep(2)
                attempt += 1
                
            except ClientError as e:
                logger.error(f"Error checking job status: {e}")
                raise
        
        raise TimeoutError(f"Job {job_id} did not complete in time")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get AWS Rekognition capabilities"""
        return {
            "provider": self.provider_type.value,
            "supported_goals": [
                AnalysisGoal.SCENE_DETECTION.value,
                AnalysisGoal.OBJECT_DETECTION.value,
                AnalysisGoal.CHARACTER_TRACKING.value,
                AnalysisGoal.TECHNICAL_ANALYSIS.value
            ],
            "max_video_size_gb": 10,
            "supports_custom_prompts": False,
            "cost_per_minute": 1.0,
            "features": [
                "shot_detection",
                "label_detection",
                "face_detection",
                "celebrity_recognition",
                "content_moderation",
                "text_detection"
            ]
        }
    
    def estimate_cost(
        self,
        duration_seconds: float,
        config: AnalysisConfig
    ) -> float:
        """Estimate cost for AWS Rekognition analysis"""
        duration_minutes = duration_seconds / 60
        return duration_minutes * 1.0  # $1 per minute