"""
Shared pytest configuration and fixtures for all tests
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from typing import Generator, AsyncGenerator
import motor.motor_asyncio
from beanie import init_beanie
from httpx import AsyncClient

# Add the backend directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_structlog():
    """Mock structlog logger to prevent logging during tests"""
    import structlog
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.debug = Mock()
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(structlog, 'get_logger', lambda: mock_logger)
        yield mock_logger


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set common environment variables for tests"""
    # Check if we're running in Docker or locally
    is_docker = os.path.exists('/.dockerenv') or os.environ.get('ENVIRONMENT') == 'test'
    
    env_vars = {
        'MONGODB_URL': os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/test'),
        'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'S3_BUCKET': 'test-bucket',
        'S3_OUTPUT_BUCKET': 'test-output-bucket',
        'OPENAI_API_KEY': 'test_openai_key',
        'NVIDIA_API_KEY': 'test_nvidia_key',
        'VECTOR_DB_TYPE': 'milvus',
        'ENVIRONMENT': 'test'
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:  # Don't override existing env vars
            monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 S3 client"""
    client = Mock()
    client.upload_file = Mock()
    client.download_file = Mock()
    client.head_object = Mock(return_value={'ContentLength': 1024})
    client.list_objects_v2 = Mock(return_value={'Contents': []})
    return client


@pytest.fixture
def mock_beanie_document():
    """Mock Beanie document methods"""
    async def mock_save(self):
        return self
    
    async def mock_delete(self):
        return None
    
    async def mock_get(cls, id):
        return None
    
    async def mock_find(cls, *args, **kwargs):
        class MockQuery:
            async def to_list(self, length=None):
                return []
            
            def sort(self, *args):
                return self
            
            def limit(self, n):
                return self
            
            def skip(self, n):
                return self
        
        return MockQuery()
    
    return {
        'save': mock_save,
        'delete': mock_delete,
        'get': mock_get,
        'find': mock_find
    }


@pytest.fixture
async def test_db():
    """Initialize test database connection"""
    from core.database import Database
    from models import Video, ProcessingJob, Scene
    
    # Connect to test database
    await Database.connect()
    
    # Initialize Beanie with test models
    await init_beanie(
        database=Database.get_database(),
        document_models=[Video, ProcessingJob, Scene]
    )
    
    yield Database.get_database()
    
    # Cleanup - drop all collections
    db = Database.get_database()
    for collection_name in await db.list_collection_names():
        await db.drop_collection(collection_name)
    
    await Database.disconnect()


@pytest.fixture
async def test_client(mock_env_vars):
    """Create test client for API testing"""
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution"""
    def _mock_task(task_func):
        mock = Mock()
        mock.delay = Mock(return_value=Mock(id="test-task-id"))
        mock.apply_async = Mock(return_value=Mock(id="test-task-id"))
        return mock
    
    with patch('celery.current_app.send_task') as mock_send:
        mock_send.return_value = Mock(id="test-task-id")
        yield _mock_task


@pytest.fixture
async def sample_video(test_db):
    """Create a sample video for testing"""
    from models import Video, VideoStatus
    
    video = Video(
        title="Test Video",
        s3_uri="s3://test-bucket/test-video.mp4",
        duration=120.0,
        status=VideoStatus.UPLOADED,
        metadata={
            "width": 1920,
            "height": 1080,
            "fps": 30
        }
    )
    await video.create()
    
    yield video
    
    # Cleanup
    await video.delete()


@pytest.fixture
def mock_s3_service(mock_boto3_client):
    """Mock S3 service for testing"""
    from services.s3_utils import S3Service
    
    with patch('boto3.client', return_value=mock_boto3_client):
        service = S3Service()
        yield service


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    import fakeredis
    
    # Create async fakeredis client
    client = fakeredis.FakeAsyncRedis()
    
    with patch('redis.asyncio.from_url', return_value=client):
        yield client


@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response"))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch('openai.AsyncOpenAI', return_value=mock_client):
        yield mock_client


# Pytest configuration for marks
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_s3: Tests requiring S3")
    config.addinivalue_line("markers", "requires_openai: Tests requiring OpenAI")
    config.addinivalue_line("markers", "requires_nvidia: Tests requiring NVIDIA")