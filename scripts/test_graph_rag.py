#!/usr/bin/env python3
"""Test Graph-RAG setup and connections"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dev-knowledge-base"))

# Load environment
load_dotenv()

print("🧪 Testing Graph-RAG Setup\n")

# Test 1: Qdrant Connection
print("1️⃣ Testing Qdrant connection...")
try:
    from qdrant_client import QdrantClient
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    
    # Get collections
    collections = client.get_collections().collections
    print(f"✅ Connected to Qdrant at {qdrant_url}")
    print(f"   Found {len(collections)} collections")
    
    # Check our collection
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")
    if any(col.name == collection_name for col in collections):
        info = client.get_collection(collection_name)
        print(f"✅ Collection '{collection_name}' exists with {info.points_count} points")
    else:
        print(f"⚠️  Collection '{collection_name}' not found")
        
except Exception as e:
    print(f"❌ Qdrant error: {e}")

# Test 2: Neo4j Connection
print("\n2️⃣ Testing Neo4j connection...")
try:
    from py2neo import Graph
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
    
    graph = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    # Test query
    result = graph.run("RETURN 1 as test").data()
    print(f"✅ Connected to Neo4j at {neo4j_uri}")
    
    # Get node count
    node_count = graph.run("MATCH (n) RETURN count(n) as count").data()[0]['count']
    print(f"   Found {node_count} total nodes")
    
except Exception as e:
    print(f"❌ Neo4j error: {e}")
    print("   Make sure Neo4j is running: docker compose up -d neo4j")

# Test 3: MongoDB Connection
print("\n3️⃣ Testing MongoDB connection...")
try:
    import motor.motor_asyncio
    import asyncio
    from beanie import init_beanie
    from models import ProjectKnowledge, ExtractionReport
    
    async def test_mongodb():
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/video-intelligence")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db_name = mongo_url.split("/")[-1].split("?")[0]
        db = client[db_name]
        
        await init_beanie(database=db, document_models=[ProjectKnowledge, ExtractionReport])
        
        count = await ProjectKnowledge.count()
        return count
    
    count = asyncio.run(test_mongodb())
    print(f"✅ Connected to MongoDB")
    print(f"   Found {count} knowledge documents")
    
except Exception as e:
    print(f"❌ MongoDB error: {e}")

# Test 4: OpenAI API
print("\n4️⃣ Testing OpenAI API...")
try:
    from langchain_openai import OpenAIEmbeddings
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
    else:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        test_embedding = embeddings.embed_query("test")
        print(f"✅ OpenAI API working")
        print(f"   Generated embedding with {len(test_embedding)} dimensions")
        
except Exception as e:
    print(f"❌ OpenAI error: {e}")

# Test 5: Dev Assistant
print("\n5️⃣ Testing Development Assistant...")
try:
    from rag.dev_assistant import DevelopmentAssistant
    
    assistant = DevelopmentAssistant()
    stats = assistant.get_statistics()
    print(f"✅ Development Assistant initialized")
    print(f"   Status: {stats.get('status', 'unknown')}")
    
except Exception as e:
    print(f"❌ Dev Assistant error: {e}")

# Test 6: Graph-RAG Assistant
print("\n6️⃣ Testing Graph-RAG Assistant...")
try:
    from rag.graph_rag_assistant import GraphRAGAssistant
    
    assistant = GraphRAGAssistant()
    stats = assistant.get_statistics()
    print(f"✅ Graph-RAG Assistant initialized")
    print(f"   Overall status: {stats.get('status', 'unknown')}")
    
except Exception as e:
    print(f"❌ Graph-RAG Assistant error: {e}")

print("\n✨ Testing complete!")
print("\nNext steps:")
print("1. If any services failed, start them with: docker compose up -d")
print("2. Run the population script: python scripts/populate_knowledge_graph.py")
print("3. Test the CLI: ./dev-cli info")