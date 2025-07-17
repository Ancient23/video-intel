#!/usr/bin/env python3
"""Test Qdrant connection and basic operations"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings

# Load environment
load_dotenv()

print("Testing Qdrant connection...")

# Connect to Qdrant
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")

try:
    client = QdrantClient(url=qdrant_url)
    print(f"✅ Connected to Qdrant at {qdrant_url}")
    
    # List collections
    collections = client.get_collections().collections
    print(f"Found {len(collections)} collections")
    for col in collections:
        print(f"  - {col.name}")
    
    # Test embeddings
    print("\nTesting OpenAI embeddings...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    test_embedding = embeddings.embed_query("Test query")
    print(f"✅ Generated embedding with {len(test_embedding)} dimensions")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()