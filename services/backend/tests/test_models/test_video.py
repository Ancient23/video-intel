"""
Test Video model
"""
import pytest
from datetime import datetime
from models.video import Video, VideoStatus
from beanie import PydanticObjectId


@pytest.mark.asyncio
@pytest.mark.integration
class TestVideoModel:
    """Test Video model operations"""
    
    async def test_create_video(self, test_db):
        """Test creating a new video"""
        video = Video(
            title="Test Video Creation",
            s3_uri="s3://test-bucket/videos/test-create.mp4",
            duration=300.5,
            status=VideoStatus.UPLOADED,
            metadata={
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "codec": "h264"
            }
        )
        
        # Save to database
        await video.create()
        
        # Verify it was saved
        assert video.id is not None
        assert isinstance(video.id, PydanticObjectId)
        assert video.created_at is not None
        assert video.updated_at is not None
        
        # Retrieve from database
        retrieved = await Video.get(video.id)
        assert retrieved is not None
        assert retrieved.title == "Test Video Creation"
        assert retrieved.duration == 300.5
        assert retrieved.metadata["width"] == 1920
        
        # Cleanup
        await video.delete()
    
    async def test_update_video_status(self, test_db):
        """Test updating video status"""
        video = Video(
            title="Test Status Update",
            s3_uri="s3://test-bucket/videos/test-status.mp4",
            duration=120.0,
            status=VideoStatus.UPLOADED
        )
        await video.create()
        
        # Update status
        video.status = VideoStatus.PROCESSING
        video.processing_started_at = datetime.utcnow()
        await video.save()
        
        # Retrieve and verify
        updated = await Video.get(video.id)
        assert updated.status == VideoStatus.PROCESSING
        assert updated.processing_started_at is not None
        
        # Cleanup
        await video.delete()
    
    async def test_find_videos_by_status(self, test_db):
        """Test finding videos by status"""
        # Create multiple videos
        videos = []
        for i in range(3):
            video = Video(
                title=f"Test Video {i}",
                s3_uri=f"s3://test-bucket/videos/test-{i}.mp4",
                duration=100.0 + i,
                status=VideoStatus.PROCESSING if i < 2 else VideoStatus.COMPLETED
            )
            await video.create()
            videos.append(video)
        
        # Find processing videos
        processing_videos = await Video.find(
            Video.status == VideoStatus.PROCESSING
        ).to_list()
        
        assert len(processing_videos) == 2
        assert all(v.status == VideoStatus.PROCESSING for v in processing_videos)
        
        # Find completed videos
        completed_videos = await Video.find(
            Video.status == VideoStatus.COMPLETED
        ).to_list()
        
        assert len(completed_videos) == 1
        assert completed_videos[0].status == VideoStatus.COMPLETED
        
        # Cleanup
        for video in videos:
            await video.delete()
    
    async def test_video_validation(self, test_db):
        """Test video model validation"""
        # Test invalid S3 URI
        with pytest.raises(ValueError):
            video = Video(
                title="Invalid Video",
                s3_uri="not-an-s3-uri",
                duration=100.0
            )
        
        # Test negative duration
        with pytest.raises(ValueError):
            video = Video(
                title="Negative Duration",
                s3_uri="s3://bucket/video.mp4",
                duration=-10.0
            )