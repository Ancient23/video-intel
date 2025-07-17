#!/usr/bin/env python3
"""Modern knowledge base population script for Video Intelligence Platform using Qdrant"""
import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import motor.motor_asyncio
from beanie import init_beanie
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dev-knowledge-base"))

# Import models
from models import ProjectKnowledge, ExtractionReport


class ModernKnowledgeExtractor:
    """Extract and process knowledge from multiple sources using Qdrant"""
    
    def __init__(self, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings
        self.embeddings = None
        self.qdrant_client = None
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        if use_embeddings:
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            self._init_qdrant()
    
    def _init_qdrant(self):
        """Initialize Qdrant client and collection"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        
        self.qdrant_client = QdrantClient(url=qdrant_url)
        print(f"✅ Connected to Qdrant at {qdrant_url}")
        
        # Create collection if it doesn't exist
        try:
            collections = self.qdrant_client.get_collections().collections
            if not any(col.name == self.collection_name for col in collections):
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created collection: {self.collection_name}")
            else:
                print(f"✅ Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"❌ Error initializing Qdrant: {e}")
            raise
    
    def _generate_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def extract_from_directory(self, directory: Path, category: str, importance: int = 3) -> List[ProjectKnowledge]:
        """Extract knowledge from markdown files in a directory"""
        knowledge_items = []
        
        for file_path in directory.rglob("*.md"):
            if file_path.name.startswith('.'):
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                if not content.strip():
                    continue
                
                # Create base knowledge item
                knowledge = ProjectKnowledge(
                    source_file=str(file_path.relative_to(project_root)),
                    source_repo="video-intelligence-platform",
                    category=category,
                    title=file_path.stem.replace('_', ' ').replace('-', ' ').title(),
                    content=content,
                    importance=importance,
                    tags=[category, file_path.parent.name],
                    created_at=datetime.utcnow()
                )
                
                knowledge_items.append(knowledge)
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
        
        return knowledge_items
    
    async def add_to_qdrant(self, knowledge_items: List[ProjectKnowledge]):
        """Add knowledge items to Qdrant with embeddings"""
        if not self.use_embeddings or not knowledge_items:
            return
        
        points = []
        point_id = int(datetime.utcnow().timestamp() * 1000)  # Start with timestamp-based ID
        
        for item in knowledge_items:
            # Generate embedding for the content
            full_text = f"{item.title}\n\n{item.content}"
            
            # Split long content into chunks
            if len(full_text) > 1000:
                chunks = self.text_splitter.split_text(full_text)
            else:
                chunks = [full_text]
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.embeddings.embed_query(chunk)
                    
                    # Create point for Qdrant
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "text": chunk,
                            "source_file": item.source_file,
                            "category": item.category,
                            "title": item.title,
                            "importance": item.importance,
                            "tags": item.tags,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "created_at": item.created_at.isoformat()
                        }
                    )
                    points.append(point)
                    point_id += 1
                    
                except Exception as e:
                    print(f"❌ Error creating embedding for {item.title}: {e}")
        
        # Upload to Qdrant in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            try:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                print(f"✅ Added {len(batch)} points to Qdrant")
            except Exception as e:
                print(f"❌ Error uploading batch to Qdrant: {e}")
    
    async def extract_internal_docs(self) -> int:
        """Extract knowledge from internal project documentation"""
        print("\n📚 Extracting internal documentation...")
        
        all_knowledge = []
        
        # Project requirements and architecture
        docs_new = project_root / "docs" / "new"
        if docs_new.exists():
            knowledge = await self.extract_from_directory(docs_new, "project_requirements", importance=5)
            all_knowledge.extend(knowledge)
            print(f"  ✅ Found {len(knowledge)} items in {docs_new}")
        
        # Deployment guides
        docs_deployment = project_root / "docs" / "deployment"
        if docs_deployment.exists():
            knowledge = await self.extract_from_directory(docs_deployment, "deployment_guides", importance=4)
            all_knowledge.extend(knowledge)
            print(f"  ✅ Found {len(knowledge)} items in {docs_deployment}")
        
        # Development knowledge base
        dev_kb = project_root / "dev-knowledge-base" / "knowledge"
        if dev_kb.exists():
            knowledge = await self.extract_from_directory(dev_kb, "development_patterns", importance=4)
            all_knowledge.extend(knowledge)
            print(f"  ✅ Found {len(knowledge)} items in {dev_kb}")
        
        # Scripts documentation
        scripts_readme = project_root / "scripts" / "README.md"
        if scripts_readme.exists():
            content = scripts_readme.read_text()
            knowledge = ProjectKnowledge(
                source_file="scripts/README.md",
                source_repo="video-intelligence-platform",
                category="implementation_patterns",
                title="Scripts Documentation",
                content=content,
                importance=3,
                tags=["scripts", "documentation"],
                created_at=datetime.utcnow()
            )
            all_knowledge.append(knowledge)
            print(f"  ✅ Added scripts documentation")
        
        # Save to MongoDB
        if all_knowledge:
            await ProjectKnowledge.insert_many(all_knowledge)
            print(f"\n✅ Saved {len(all_knowledge)} items to MongoDB")
            
            # Add to Qdrant
            await self.add_to_qdrant(all_knowledge)
        
        return len(all_knowledge)
    
    def add_curated_resources(self) -> List[Dict[str, Any]]:
        """Add curated external resources"""
        resources = [
            {
                "title": "AWS Rekognition Video Documentation",
                "content": "AWS Rekognition Video provides video analysis capabilities including object detection, face detection, celebrity recognition, text detection, and content moderation. Key features: Shot detection, Technical cue detection (black frames, end credits), Segment detection.",
                "category": "video_processing",
                "importance": 4,
                "tags": ["aws", "rekognition", "video-analysis"]
            },
            {
                "title": "OpenAI Vision API Guide",
                "content": "GPT-4 Vision enables understanding of images alongside text. Best practices: Use high-res mode for detailed analysis, Combine with function calling for structured output, Process video frames at strategic intervals.",
                "category": "multimodal_ai",
                "importance": 4,
                "tags": ["openai", "vision", "gpt-4"]
            },
            {
                "title": "MongoDB Atlas Vector Search",
                "content": "MongoDB Atlas Search supports vector similarity search with HNSW algorithm. Features: Hybrid search combining vectors and filters, Integration with popular embedding models, Scalable infrastructure.",
                "category": "architecture_patterns",
                "importance": 3,
                "tags": ["mongodb", "vector-search", "atlas"]
            },
            {
                "title": "Celery Canvas Workflows",
                "content": "Celery Canvas provides workflow primitives: group() for parallel execution, chain() for sequential tasks, chord() for synchronization. Best for video processing pipelines.",
                "category": "implementation_patterns",
                "importance": 4,
                "tags": ["celery", "workflow", "parallel-processing"]
            },
            {
                "title": "FFmpeg Video Processing",
                "content": "FFmpeg is essential for video manipulation. Key operations: Scene detection with scene filter, Keyframe extraction with select filter, Format conversion and compression.",
                "category": "video_processing",
                "importance": 5,
                "tags": ["ffmpeg", "video", "processing"]
            }
        ]
        
        return resources
    
    async def add_curated_to_db(self, resources: List[Dict[str, Any]]) -> int:
        """Add curated resources to database"""
        print("\n🌟 Adding curated resources...")
        
        knowledge_items = []
        for resource in resources:
            knowledge = ProjectKnowledge(
                source_file="curated_resources",
                source_repo="external",
                category=resource["category"],
                title=resource["title"],
                content=resource["content"],
                importance=resource["importance"],
                tags=resource["tags"],
                created_at=datetime.utcnow()
            )
            knowledge_items.append(knowledge)
        
        if knowledge_items:
            await ProjectKnowledge.insert_many(knowledge_items)
            print(f"✅ Added {len(knowledge_items)} curated resources to MongoDB")
            
            # Add to Qdrant
            await self.add_to_qdrant(knowledge_items)
        
        return len(knowledge_items)


async def main():
    """Main extraction workflow"""
    print("🚀 Starting Modern Knowledge Base Population with Qdrant\n")
    
    # Load environment
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables")
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/video-intelligence")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    db = client.get_database()
    
    await init_beanie(
        database=db,
        document_models=[ProjectKnowledge, ExtractionReport]
    )
    print("✅ Connected to MongoDB\n")
    
    # Initialize extractor
    extractor = ModernKnowledgeExtractor(use_embeddings=True)
    
    # Extract internal documentation
    internal_count = await extractor.extract_internal_docs()
    
    # Add curated resources
    resources = extractor.add_curated_resources()
    curated_count = await extractor.add_curated_to_db(resources)
    
    # Create extraction report
    report = ExtractionReport(
        extraction_type="modern_knowledge_base",
        source="internal_and_curated",
        total_items=internal_count + curated_count,
        categories={
            "internal_docs": internal_count,
            "curated_resources": curated_count
        },
        metadata={
            "extractor": "ModernKnowledgeExtractor",
            "use_embeddings": True,
            "vector_db": "qdrant"
        }
    )
    await report.insert()
    
    # Get statistics
    total_kb = await ProjectKnowledge.count()
    
    if extractor.qdrant_client:
        try:
            collection_info = extractor.qdrant_client.get_collection(extractor.collection_name)
            qdrant_count = collection_info.points_count
            print(f"\n📊 Qdrant Statistics:")
            print(f"  - Collection: {extractor.collection_name}")
            print(f"  - Total points: {qdrant_count}")
            print(f"  - Vector size: {collection_info.config.params.vectors.size}")
        except Exception as e:
            print(f"\n❌ Could not get Qdrant statistics: {e}")
    
    print(f"\n📊 Final Statistics:")
    print(f"  - Total items in MongoDB: {total_kb}")
    print(f"  - Items added this run: {internal_count + curated_count}")
    print(f"    - Internal docs: {internal_count}")
    print(f"    - Curated resources: {curated_count}")
    
    print("\n✨ Modern knowledge base population complete!")


if __name__ == "__main__":
    asyncio.run(main())