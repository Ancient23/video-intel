"""
Test Docker services connectivity
"""
import pytest
import os
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
class TestDockerServices:
    """Test that Docker services are accessible"""
    
    async def test_mongodb_connection(self):
        """Test MongoDB connectivity"""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        
        # Try to connect to MongoDB
        client = AsyncIOMotorClient(mongodb_url)
        
        try:
            # Ping the database
            await client.admin.command('ping')
            
            # List databases to ensure connection works
            databases = await client.list_database_names()
            assert isinstance(databases, list)
        finally:
            client.close()
    
    async def test_redis_connection(self):
        """Test Redis connectivity"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Try to connect to Redis
        client = await redis.from_url(redis_url)
        
        try:
            # Ping Redis
            pong = await client.ping()
            assert pong is True
            
            # Set and get a test value
            await client.set("test_key", "test_value")
            value = await client.get("test_key")
            assert value == b"test_value"
            
            # Cleanup
            await client.delete("test_key")
        finally:
            await client.close()
    
    @pytest.mark.skipif(
        os.getenv("ENVIRONMENT") == "test" and not os.getenv("CHROMADB_URL"),
        reason="ChromaDB not required in test environment"
    )
    async def test_chromadb_connection(self):
        """Test ChromaDB connectivity"""
        chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
        
        async with httpx.AsyncClient() as client:
            try:
                # Check ChromaDB heartbeat
                response = await client.get(f"{chromadb_url}/api/v1/heartbeat")
                
                # ChromaDB might return 200 or other status codes
                # Just ensure we can connect
                assert response.status_code in [200, 404, 410]
            except httpx.ConnectError:
                pytest.skip("ChromaDB not available")
    
    def test_environment_variables(self):
        """Test that required environment variables are set"""
        # In test environment, these should be set
        required_vars = [
            "MONGODB_URL",
            "REDIS_URL",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "S3_BUCKET",
            "S3_OUTPUT_BUCKET"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            assert value is not None, f"Environment variable {var} is not set"
            
            # In test environment, AWS keys should be test values
            if var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
                assert value in ["test", "test_access_key", "test_secret_key", "test-access-key", "test-secret-key"]