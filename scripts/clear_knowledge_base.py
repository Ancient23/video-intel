#!/usr/bin/env python3
"""Script to clear ChromaDB and MongoDB knowledge base data"""
import os
import sys
import shutil
import asyncio
from pathlib import Path
import motor.motor_asyncio
from beanie import init_beanie
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dev-knowledge-base"))

# Import models
from models import ProjectKnowledge, ExtractionReport


async def clear_mongodb():
    """Clear MongoDB collections"""
    print("🗑️  Clearing MongoDB collections...")
    
    # Initialize MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    
    await init_beanie(
        database=client.dev_knowledge_base,
        document_models=[ProjectKnowledge, ExtractionReport]
    )
    
    # Delete all documents
    deleted_knowledge = await ProjectKnowledge.delete_all()
    deleted_reports = await ExtractionReport.delete_all()
    
    print(f"   ✓ Deleted {deleted_knowledge.deleted_count} knowledge items")
    print(f"   ✓ Deleted {deleted_reports.deleted_count} extraction reports")


def clear_chromadb():
    """Clear ChromaDB collections"""
    print("🗑️  Clearing ChromaDB collections...")
    
    # Check environment for ChromaDB client type
    chroma_type = os.getenv("CHROMA_CLIENT_TYPE", "persistent")
    
    if chroma_type == "persistent":
        # For persistent client, we can just delete the directory
        chroma_path = os.getenv("CHROMA_PERSIST_PATH", "./knowledge/chromadb")
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            print(f"   ✓ Deleted ChromaDB directory: {chroma_path}")
        else:
            print(f"   ℹ️  ChromaDB directory not found: {chroma_path}")
    else:
        # For HTTP client, connect and delete collections
        client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000")),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get all collections
        collections = client.list_collections()
        
        for collection in collections:
            client.delete_collection(collection.name)
            print(f"   ✓ Deleted collection: {collection.name}")
        
        if not collections:
            print("   ℹ️  No collections found")


async def main():
    """Main function"""
    print("🧹 Clearing Video Intelligence Knowledge Base\n")
    
    # Load environment variables
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables\n")
    
    # Clear MongoDB
    try:
        await clear_mongodb()
    except Exception as e:
        print(f"❌ Error clearing MongoDB: {e}")
    
    # Clear ChromaDB
    try:
        clear_chromadb()
    except Exception as e:
        print(f"❌ Error clearing ChromaDB: {e}")
    
    print("\n✨ Knowledge base cleared successfully!")


if __name__ == "__main__":
    asyncio.run(main())