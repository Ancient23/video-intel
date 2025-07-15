"""
Shared pytest configuration and fixtures for all tests
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock

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
    env_vars = {
        'MONGODB_URL': 'mongodb://localhost:27017/test',
        'REDIS_URL': 'redis://localhost:6379/0',
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'S3_BUCKET': 'test-bucket',
        'S3_OUTPUT_BUCKET': 'test-output-bucket',
        'OPENAI_API_KEY': 'test_openai_key',
        'NVIDIA_API_KEY': 'test_nvidia_key',
        'VECTOR_DB_TYPE': 'milvus'
    }
    
    for key, value in env_vars.items():
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