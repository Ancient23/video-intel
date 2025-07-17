#!/usr/bin/env python3
"""Simple Qdrant population script without async MongoDB"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

class SimpleKnowledgePopulator:
    """Simple knowledge base populator for Qdrant"""
    
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")
        self.client = QdrantClient(url=self.qdrant_url)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
    def create_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        if not any(col.name == self.collection_name for col in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {self.collection_name}")
        else:
            print(f"✅ Collection exists: {self.collection_name}")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to Qdrant"""
        points = []
        
        for i, doc in enumerate(documents):
            text = f"{doc['title']}\n\n{doc['content']}"
            
            # Generate embedding
            try:
                embedding = self.embeddings.embed_query(text)
                
                point = PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "text": text,
                        "title": doc['title'],
                        "category": doc['category'],
                        "source": doc.get('source', 'unknown'),
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
                points.append(point)
            except Exception as e:
                print(f"❌ Error creating embedding: {e}")
        
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"✅ Added {len(points)} documents to Qdrant")
    
    def populate_basic_knowledge(self):
        """Populate with basic knowledge for testing"""
        documents = [
            {
                "title": "Video Intelligence Platform Overview",
                "content": "The Video Intelligence Platform is a comprehensive system for video analysis using AI. It processes videos to extract insights, generate summaries, and enable intelligent conversations about video content.",
                "category": "overview",
                "source": "project_docs"
            },
            {
                "title": "Architecture Overview",
                "content": "The platform uses a two-phase architecture: 1) Ingestion Phase - Heavy preprocessing to extract all possible information, 2) Runtime Phase - Lightweight retrieval and generation for real-time chat. It uses MongoDB for structured storage and Qdrant for vector embeddings.",
                "category": "architecture",
                "source": "project_docs"
            },
            {
                "title": "Video Processing Pipeline",
                "content": "Videos are processed through: 1) Chunking - Intelligent segmentation using shot detection, 2) Analysis - Multi-modal analysis with VLMs and object detection, 3) Knowledge Graph - Entity and relationship extraction, 4) Embedding - Vector representations for semantic search.",
                "category": "video_processing",
                "source": "project_docs"
            },
            {
                "title": "Development Setup",
                "content": "To set up the development environment: 1) Start Docker services (MongoDB, Redis, Qdrant), 2) Install Python dependencies, 3) Configure environment variables, 4) Run population scripts to build knowledge base.",
                "category": "development",
                "source": "project_docs"
            },
            {
                "title": "AWS Deployment",
                "content": "The platform is designed for AWS deployment using: ECS/Fargate for containerized services, S3 for video storage, CloudFront for CDN, MongoDB Atlas for managed database, Qdrant Cloud or self-hosted for vector search.",
                "category": "deployment",
                "source": "project_docs"
            }
        ]
        
        # Read actual project files if they exist
        prd_path = project_root / "docs" / "new" / "video-intelligence-prd.md"
        if prd_path.exists():
            try:
                content = prd_path.read_text()[:2000]  # First 2000 chars
                documents.append({
                    "title": "Product Requirements Document",
                    "content": content,
                    "category": "requirements",
                    "source": str(prd_path.relative_to(project_root))
                })
                print(f"✅ Added PRD from {prd_path}")
            except Exception as e:
                print(f"❌ Error reading PRD: {e}")
        
        return documents

def main():
    print("🚀 Simple Qdrant Knowledge Base Population\n")
    
    populator = SimpleKnowledgePopulator()
    
    # Create collection
    populator.create_collection()
    
    # Get documents
    documents = populator.populate_basic_knowledge()
    print(f"\nFound {len(documents)} documents to add")
    
    # Add to Qdrant
    populator.add_documents(documents)
    
    # Get statistics
    collection_info = populator.client.get_collection(populator.collection_name)
    print(f"\n📊 Collection Statistics:")
    print(f"  - Name: {populator.collection_name}")
    print(f"  - Points: {collection_info.points_count}")
    print(f"  - Vector size: {collection_info.config.params.vectors.size}")
    
    print("\n✨ Population complete!")

if __name__ == "__main__":
    main()