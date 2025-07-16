#!/usr/bin/env python3
"""Modern knowledge base population script for Video Intelligence Platform"""
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
import chromadb
from chromadb.config import Settings
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
    """Extract and process knowledge from multiple sources"""
    
    def __init__(self, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings
        self.embeddings = None
        self.chroma_client = None
        self.collections = {}
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        if use_embeddings:
            self.embeddings = OpenAIEmbeddings()
            self._init_chromadb()
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and collections"""
        chroma_type = os.getenv("CHROMA_CLIENT_TYPE", "persistent")
        
        if chroma_type == "http":
            self.chroma_client = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", "localhost"),
                port=int(os.getenv("CHROMA_PORT", "8000")),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.chroma_client = chromadb.PersistentClient(
                path=os.getenv("CHROMA_PERSIST_PATH", "./knowledge/chromadb"),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        
        # Define collections for the Video Intelligence Platform
        collection_configs = {
            "project_requirements": "Core project requirements and architecture",
            "implementation_patterns": "Code patterns and implementation guides",
            "deployment_guides": "Deployment and infrastructure patterns",
            "video_processing": "Video processing and AI techniques",
            "api_documentation": "API endpoints and integration patterns",
            "best_practices": "Best practices and optimization techniques",
            "known_issues": "Known issues and technical debt"
        }
        
        for name, description in collection_configs.items():
            self.collections[name] = self.chroma_client.create_collection(
                name=name,
                metadata={"description": description}
            )
    
    def _generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for content"""
        return hashlib.md5(f"{content[:100]}{source}".encode()).hexdigest()
    
    async def extract_project_documentation(self, docs_path: Path) -> Dict[str, List[Dict]]:
        """Extract knowledge from project documentation"""
        print(f"\n📚 Extracting project documentation from {docs_path}")
        extracted = {
            "project_requirements": [],
            "deployment_guides": [],
            "known_issues": [],
            "implementation_patterns": []
        }
        
        # Map file patterns to categories
        file_mappings = {
            "**/*prd*.md": "project_requirements",
            "**/deployment/*.md": "deployment_guides",
            "**/TECHNICAL_DEBT.md": "known_issues",
            "**/PROJECT_MANAGEMENT.md": "project_requirements",
            "**/testing/*.md": "implementation_patterns",
            "**/DEVELOPER_*.md": "implementation_patterns"
        }
        
        for pattern, category in file_mappings.items():
            for file_path in docs_path.glob(pattern):
                if file_path.is_file():
                    print(f"  📄 Processing {file_path.name}")
                    
                    content = file_path.read_text(encoding='utf-8')
                    chunks = self.text_splitter.split_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "source_file": str(file_path.relative_to(project_root)),
                            "category": category,
                            "title": f"{file_path.stem} - Part {i+1}",
                            "content": chunk,
                            "importance": 5 if "prd" in file_path.name.lower() else 4,
                            "tags": [category, file_path.stem.lower()]
                        }
                        extracted[category].append(doc)
                        
                        # Add to ChromaDB if embeddings enabled
                        if self.use_embeddings and category in self.collections:
                            self._add_to_chromadb(doc, category)
        
        return extracted
    
    def _add_to_chromadb(self, doc: Dict, category: str):
        """Add document to ChromaDB collection"""
        try:
            doc_id = self._generate_id(doc["content"], doc["source_file"])
            
            self.collections[category].add(
                documents=[doc["content"]],
                metadatas=[{
                    "source": doc["source_file"],
                    "title": doc["title"],
                    "tags": ",".join(doc.get("tags", [])),
                    "importance": doc.get("importance", 3)
                }],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"    ⚠️  Error adding to ChromaDB: {e}")
    
    async def extract_implementation_files(self, src_path: Path) -> Dict[str, List[Dict]]:
        """Extract patterns from implementation files"""
        print(f"\n💻 Extracting implementation patterns from {src_path}")
        extracted = {"implementation_patterns": []}
        
        # Focus on key implementation files
        patterns = [
            "services/backend/services/**/*.py",
            "services/backend/api/**/*.py",
            "services/backend/schemas/**/*.py",
            "services/backend/models/**/*.py"
        ]
        
        for pattern in patterns:
            for file_path in src_path.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith("__"):
                    print(f"  🐍 Processing {file_path.name}")
                    
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        
                        # Extract docstrings and important patterns
                        if len(content) > 100:  # Skip empty files
                            # For now, just take the first part of the file
                            # In future, could parse AST for better extraction
                            chunk = content[:2000]
                            
                            doc = {
                                "source_file": str(file_path.relative_to(project_root)),
                                "category": "implementation_patterns",
                                "title": f"{file_path.stem} implementation",
                                "content": chunk,
                                "importance": 3,
                                "tags": ["implementation", file_path.parent.name, "python"]
                            }
                            extracted["implementation_patterns"].append(doc)
                            
                            if self.use_embeddings:
                                self._add_to_chromadb(doc, "implementation_patterns")
                    
                    except Exception as e:
                        print(f"    ⚠️  Error processing {file_path.name}: {e}")
        
        return extracted
    
    def add_curated_resources(self) -> Dict[str, List[Dict]]:
        """Add curated external resources"""
        print("\n🌐 Adding curated external resources")
        
        resources = {
            "video_processing": [
                {
                    "title": "FFmpeg Video Processing Fundamentals",
                    "content": """FFmpeg is the foundation for video processing. Key concepts:
                    - Video codecs (H.264, H.265, VP9) affect quality and compatibility
                    - Container formats (MP4, MKV, WebM) determine feature support
                    - Keyframes are essential for seeking and chunking
                    - Use -ss for fast seeking, -t for duration
                    - Hardware acceleration with -hwaccel for performance
                    - Scene detection with select filter
                    - Thumbnail extraction with fps filter
                    Example: ffmpeg -i input.mp4 -ss 00:00:10 -t 00:00:05 -c copy output.mp4""",
                    "source_file": "external/ffmpeg-guide",
                    "importance": 5,
                    "tags": ["video", "ffmpeg", "processing"]
                },
                {
                    "title": "OpenCV for Video Analysis",
                    "content": """OpenCV provides computer vision capabilities for video:
                    - cv2.VideoCapture() for reading video frames
                    - Frame-by-frame processing for custom analysis
                    - Shot boundary detection using histogram differences
                    - Object detection and tracking across frames
                    - Optical flow for motion analysis
                    - Face detection and recognition
                    - Background subtraction for motion detection
                    Best practice: Process frames in batches for GPU efficiency""",
                    "source_file": "external/opencv-patterns",
                    "importance": 4,
                    "tags": ["video", "opencv", "computer-vision"]
                }
            ],
            "best_practices": [
                {
                    "title": "Video Chunking Best Practices",
                    "content": """Effective video chunking strategies:
                    - Use scene detection for natural boundaries
                    - Overlap chunks by 1-2 seconds to avoid missing context
                    - Chunk size depends on use case (5-30 seconds typical)
                    - Store chunk metadata separately from video files
                    - Use consistent naming: video_id/chunk_000.mp4
                    - Generate thumbnails for each chunk
                    - Cache processed chunks to avoid reprocessing
                    - Use parallel processing but limit concurrent jobs
                    - Monitor memory usage with large videos""",
                    "source_file": "external/chunking-practices",
                    "importance": 5,
                    "tags": ["video", "chunking", "best-practices"]
                },
                {
                    "title": "RAG System Design for Video",
                    "content": """Building RAG systems for video content:
                    - Multi-modal embeddings combine visual and text
                    - Temporal context is crucial - include timestamps
                    - Hierarchical indexing: video -> scene -> shot -> frame
                    - Dense captions provide better retrieval than sparse labels
                    - Knowledge graphs capture entity relationships
                    - Vector similarity alone isn't enough - use hybrid search
                    - Chunk embeddings should overlap for continuity
                    - Cache frequently accessed embeddings
                    - Use metadata filters before similarity search""",
                    "source_file": "external/video-rag-patterns",
                    "importance": 5,
                    "tags": ["rag", "video", "embeddings"]
                }
            ],
            "api_documentation": [
                {
                    "title": "AWS Rekognition Video API Patterns",
                    "content": """AWS Rekognition for video analysis:
                    - StartSegmentDetection for shot/scene detection
                    - StartLabelDetection for object and activity recognition
                    - StartFaceDetection for face tracking
                    - StartTextDetection for on-screen text
                    - Async processing with SNS notifications
                    - Pagination for large result sets
                    - Cost optimization: $0.10 per minute analyzed
                    - Use S3 for video storage, not direct upload
                    - Results expire after 7 days - store them""",
                    "source_file": "external/aws-rekognition-guide",
                    "importance": 4,
                    "tags": ["aws", "rekognition", "api"]
                }
            ]
        }
        
        # Add resources to MongoDB and ChromaDB
        extracted = {}
        for category, items in resources.items():
            extracted[category] = []
            for item in items:
                print(f"  📌 Adding {item['title']}")
                item["category"] = category
                extracted[category].append(item)
                
                if self.use_embeddings and category in self.collections:
                    self._add_to_chromadb(item, category)
        
        return extracted


async def store_in_mongodb(extracted_data: Dict[str, List[Dict]], report: ExtractionReport) -> int:
    """Store extracted knowledge in MongoDB"""
    print("\n💾 Storing in MongoDB...")
    stored_count = 0
    
    for category, items in extracted_data.items():
        for item in items:
            try:
                knowledge = ProjectKnowledge(
                    source_file=item["source_file"],
                    source_repo="video-intelligence-project",
                    category=category,
                    title=item["title"],
                    content=item["content"],
                    tags=item.get("tags", []),
                    importance=item.get("importance", 3),
                    date_extracted=datetime.now()
                )
                await knowledge.insert()
                stored_count += 1
            except Exception as e:
                report.errors.append(f"Error storing {item['title']}: {str(e)}")
    
    return stored_count


async def main():
    """Main function"""
    print("🚀 Modern Video Intelligence Knowledge Base Population\n")
    
    # Load environment variables
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables")
    
    # Check for OpenAI API key
    use_embeddings = bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your-api-key")
    if not use_embeddings:
        print("⚠️  No OpenAI API key found - skipping embeddings generation")
    
    # Initialize MongoDB
    try:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
        await init_beanie(
            database=client.dev_knowledge_base,
            document_models=[ProjectKnowledge, ExtractionReport]
        )
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Create extraction report
    report = ExtractionReport(
        extraction_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        old_repo_path="N/A - Using modern sources",
        pdf_dir="N/A - Using curated content",
        started_at=datetime.now()
    )
    await report.insert()
    
    # Initialize extractor
    extractor = ModernKnowledgeExtractor(use_embeddings=use_embeddings)
    
    all_extracted = {}
    
    try:
        # 1. Extract project documentation
        docs_extracted = await extractor.extract_project_documentation(
            project_root / "docs"
        )
        for category, items in docs_extracted.items():
            all_extracted.setdefault(category, []).extend(items)
        
        # 2. Extract implementation patterns
        impl_extracted = await extractor.extract_implementation_files(
            project_root / "services"
        )
        for category, items in impl_extracted.items():
            all_extracted.setdefault(category, []).extend(items)
        
        # 3. Add curated external resources
        curated = extractor.add_curated_resources()
        for category, items in curated.items():
            all_extracted.setdefault(category, []).extend(items)
        
        # Store in MongoDB
        stored_count = await store_in_mongodb(all_extracted, report)
        
        # Update report
        report.statistics = {
            "categories_populated": list(all_extracted.keys()),
            "items_by_category": {k: len(v) for k, v in all_extracted.items()},
            "total_items": sum(len(v) for v in all_extracted.values()),
            "total_stored": stored_count,
            "embeddings_generated": use_embeddings
        }
        report.status = "completed"
        report.completed_at = datetime.now()
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  - Categories populated: {len(all_extracted)}")
        print(f"  - Total items extracted: {sum(len(v) for v in all_extracted.values())}")
        print(f"  - Items stored in MongoDB: {stored_count}")
        print(f"  - Embeddings generated: {'Yes' if use_embeddings else 'No'}")
        
        print("\n📈 Items by category:")
        for category, items in sorted(all_extracted.items()):
            print(f"  - {category}: {len(items)} items")
        
    except Exception as e:
        report.status = "failed"
        report.errors.append(f"Fatal error: {str(e)}")
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await report.save()
    
    print("\n✨ Knowledge base population complete!")


if __name__ == "__main__":
    asyncio.run(main())