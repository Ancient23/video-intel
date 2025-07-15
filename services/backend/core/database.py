import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from ..models import document_models


class Database:
    """MongoDB database connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB and initialize Beanie"""
        # Get MongoDB URL from environment
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "video_intelligence")
        
        # Create Motor client
        cls.client = AsyncIOMotorClient(mongodb_url)
        
        # Initialize Beanie with document models
        await init_beanie(
            database=cls.client[database_name],
            document_models=document_models
        )
        
        print(f"Connected to MongoDB: {mongodb_url}/{database_name}")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            print("Disconnected from MongoDB")
    
    @classmethod
    async def ping(cls) -> bool:
        """Check if database is accessible"""
        try:
            if cls.client:
                await cls.client.admin.command('ping')
                return True
        except Exception as e:
            print(f"Database ping failed: {e}")
        return False
    
    @classmethod
    async def create_indexes(cls):
        """Ensure all indexes are created"""
        for model in document_models:
            await model.create_indexes()
        print("Database indexes created")


# Convenience functions
async def get_database():
    """Get database instance for dependency injection"""
    if not Database.client:
        await Database.connect()
    return Database.client


async def init_database():
    """Initialize database connection and indexes"""
    await Database.connect()
    await Database.create_indexes()