#!/usr/bin/env python3
"""Test ChromaDB connection"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Loaded environment variables")

print("Testing ChromaDB...")

try:
    import chromadb
    print("✅ ChromaDB imported successfully")
    
    # Test creating a client
    chroma_type = os.getenv("CHROMA_CLIENT_TYPE", "persistent")
    print(f"ChromaDB type: {chroma_type}")
    
    if chroma_type == "persistent":
        client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_PERSIST_PATH", "./knowledge/chromadb")
        )
        print("✅ Created PersistentClient")
    else:
        client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8000"))
        )
        print("✅ Created HttpClient")
    
    # List collections
    collections = client.list_collections()
    print(f"✅ Listed collections: {len(collections)} found")
    
    # Try to create a test collection
    test_collection = client.create_collection("test_collection")
    print("✅ Created test collection")
    
    # Delete test collection
    client.delete_collection("test_collection")
    print("✅ Deleted test collection")
    
    print("\n✨ ChromaDB is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()