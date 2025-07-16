"""
Video Chunker - Downloads and chunks videos for analysis
"""
import os
import tempfile
import shutil
from typing import List, Optional, Tuple
import ffmpeg
import boto3
from botocore.exceptions import ClientError
import structlog
from pathlib import Path

from schemas.analysis import ChunkInfo, AnalysisConfig
from models import Video, ProcessingJob

logger = structlog.get_logger()


class VideoChunker:
    """Handles video downloading and chunking"""
    
    def __init__(self, s3_client=None, temp_dir: Optional[str] = None):
        self.s3_client = s3_client or boto3.client('s3')
        self.temp_base_dir = temp_dir or tempfile.gettempdir()
        self.current_temp_dir = None
        
    def process_video(
        self,
        video_s3_uri: str,
        config: AnalysisConfig,
        processing_job: Optional[ProcessingJob] = None
    ) -> List[ChunkInfo]:
        """
        Download and chunk video based on analysis configuration
        
        Args:
            video_s3_uri: S3 URI of the video
            config: Analysis configuration
            processing_job: Optional job to track progress
            
        Returns:
            List of chunk information
        """
        try:
            # Create temporary directory for this job
            self.current_temp_dir = tempfile.mkdtemp(
                prefix="video_chunk_", 
                dir=self.temp_base_dir
            )
            
            # Download video
            if processing_job:
                # Note: This is called from sync context in some cases
                # The orchestration service handles the async save
                processing_job.progress = 10
                processing_job.current_step = "Downloading video"
            
            local_video_path = self._download_video(video_s3_uri)
            
            # Get video info
            video_info = self._get_video_info(local_video_path)
            duration = video_info['duration']
            
            if processing_job:
                processing_job.progress = 20
                processing_job.current_step = "Creating chunks"
            
            # Create chunks
            chunks = self._create_chunks(
                local_video_path,
                duration,
                config.chunk_duration,
                config.chunk_overlap
            )
            
            # Extract keyframes for each chunk
            if processing_job:
                processing_job.progress = 40
                processing_job.current_step = "Extracting keyframes"
                
            chunk_infos = []
            for i, (start, end) in enumerate(chunks):
                chunk_info = self._process_chunk(
                    local_video_path,
                    i,
                    start,
                    end,
                    video_s3_uri
                )
                chunk_infos.append(chunk_info)
                
                if processing_job and i % 5 == 0:
                    progress = 40 + (40 * i / len(chunks))
                    processing_job.progress = progress
                    processing_job.current_step = f"Processing chunk {i+1}/{len(chunks)}"
            
            logger.info(
                "Video chunking completed",
                num_chunks=len(chunk_infos),
                video_duration=duration
            )
            
            return chunk_infos
            
        except Exception as e:
            logger.error("Video chunking failed", error=str(e))
            raise
        finally:
            # Cleanup will be called separately after all processing
            pass
    
    def _download_video(self, s3_uri: str) -> str:
        """Download video from S3 to local temp directory"""
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        
        parts = s3_uri[5:].split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        
        bucket, key = parts
        local_path = os.path.join(self.current_temp_dir, "source_video.mp4")
        
        logger.info("Downloading video from S3", bucket=bucket, key=key)
        
        try:
            self.s3_client.download_file(bucket, key, local_path)
            return local_path
        except ClientError as e:
            logger.error("Failed to download from S3", error=str(e))
            raise
    
    def _get_video_info(self, video_path: str) -> dict:
        """Get video information using ffprobe"""
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            duration = float(probe['format']['duration'])
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            fps = eval(video_stream['avg_frame_rate'])  # e.g., "30/1" -> 30.0
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps,
                'codec': video_stream.get('codec_name', 'unknown')
            }
            
        except ffmpeg.Error as e:
            logger.error("FFmpeg probe failed", error=str(e))
            raise
    
    def _create_chunks(
        self,
        video_path: str,
        duration: float,
        chunk_duration: int,
        overlap: int
    ) -> List[Tuple[float, float]]:
        """Calculate chunk boundaries with overlap"""
        chunks = []
        start = 0.0
        
        while start < duration:
            end = min(start + chunk_duration, duration)
            chunks.append((start, end))
            
            # Move to next chunk with overlap
            start = end - overlap if end < duration else duration
            
            # Avoid tiny last chunk
            if duration - start < 3:  # Less than 3 seconds
                if chunks:
                    # Extend the last chunk
                    chunks[-1] = (chunks[-1][0], duration)
                break
        
        return chunks
    
    def _process_chunk(
        self,
        video_path: str,
        chunk_index: int,
        start_time: float,
        end_time: float,
        original_s3_uri: str
    ) -> ChunkInfo:
        """Process a single chunk - extract and save"""
        chunk_id = f"chunk_{chunk_index:04d}"
        duration = end_time - start_time
        
        # Local paths
        chunk_path = os.path.join(self.current_temp_dir, f"{chunk_id}.mp4")
        keyframe_path = os.path.join(self.current_temp_dir, f"{chunk_id}_keyframe.jpg")
        
        # Extract chunk using ffmpeg
        try:
            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(chunk_path, c='copy', avoid_negative_ts='make_zero')
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as e:
            logger.error(f"Failed to extract chunk {chunk_id}", error=str(e))
            raise
        
        # Extract keyframe (middle of chunk)
        keyframe_time = duration / 2
        try:
            (
                ffmpeg
                .input(chunk_path, ss=keyframe_time)
                .output(keyframe_path, vframes=1)
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as e:
            logger.warning(f"Failed to extract keyframe for {chunk_id}", error=str(e))
            keyframe_path = None
        
        # Upload to S3 (same bucket, different prefix)
        bucket, original_key = self._parse_s3_uri(original_s3_uri)
        video_id = Path(original_key).stem
        
        chunk_s3_key = f"videos/{video_id}/chunks/{chunk_id}.mp4"
        chunk_s3_uri = self._upload_to_s3(chunk_path, bucket, chunk_s3_key)
        
        keyframe_s3_uri = None
        if keyframe_path:
            keyframe_s3_key = f"videos/{video_id}/keyframes/{chunk_id}.jpg"
            keyframe_s3_uri = self._upload_to_s3(keyframe_path, bucket, keyframe_s3_key)
        
        return ChunkInfo(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            local_path=chunk_path,
            s3_uri=chunk_s3_uri,
            keyframe_path=keyframe_s3_uri
        )
    
    def _parse_s3_uri(self, s3_uri: str) -> Tuple[str, str]:
        """Parse S3 URI into bucket and key"""
        parts = s3_uri[5:].split('/', 1)
        return parts[0], parts[1]
    
    def _upload_to_s3(self, local_path: str, bucket: str, key: str) -> str:
        """Upload file to S3 and return URI"""
        try:
            self.s3_client.upload_file(local_path, bucket, key)
            return f"s3://{bucket}/{key}"
        except ClientError as e:
            logger.error("Failed to upload to S3", error=str(e), key=key)
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.current_temp_dir and os.path.exists(self.current_temp_dir):
            try:
                shutil.rmtree(self.current_temp_dir)
                logger.info("Cleaned up temp directory", path=self.current_temp_dir)
            except Exception as e:
                logger.warning("Failed to cleanup temp directory", error=str(e))
            finally:
                self.current_temp_dir = None