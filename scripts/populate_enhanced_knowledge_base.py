#!/usr/bin/env python3
"""Enhanced knowledge base population with PDFs and GitHub repositories"""
import asyncio
import os
import sys
import json
import shutil
import tempfile
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
import PyPDF2
import requests
from git import Repo
import re

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dev-knowledge-base"))

# Import models
from models import ProjectKnowledge, ExtractionReport


class EnhancedKnowledgeExtractor:
    """Extract knowledge from PDFs, GitHub repos, and other sources"""
    
    def __init__(self, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings
        self.embeddings = None
        self.chroma_client = None
        self.collections = {}
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""]
        )
        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
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
        
        # Extended collections for new content types
        collection_configs = {
            "project_requirements": "Core project requirements and architecture",
            "implementation_patterns": "Code patterns and implementation guides",
            "deployment_guides": "Deployment and infrastructure patterns",
            "video_processing": "Video processing and AI techniques",
            "architecture_patterns": "System design and architecture blueprints",
            "multimodal_ai": "Vision-language and multi-modal AI patterns",
            "production_patterns": "Production deployment and scaling patterns",
            "api_documentation": "API endpoints and integration patterns",
            "best_practices": "Best practices and optimization techniques",
            "known_issues": "Known issues and technical debt"
        }
        
        # Get existing collections
        existing_collections = {c.name for c in self.chroma_client.list_collections()}
        
        for name, description in collection_configs.items():
            if name in existing_collections:
                self.collections[name] = self.chroma_client.get_collection(name)
            else:
                self.collections[name] = self.chroma_client.create_collection(
                    name=name,
                    metadata={"description": description}
                )
    
    def _generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for content"""
        return hashlib.md5(f"{content[:100]}{source}".encode()).hexdigest()
    
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
                    "importance": doc.get("importance", 3),
                    "source_type": doc.get("source_type", "unknown")
                }],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"    ⚠️  Error adding to ChromaDB: {e}")
    
    async def extract_pdf_knowledge(self, pdf_path: Path) -> Dict[str, List[Dict]]:
        """Extract knowledge from PDF files"""
        print(f"\n📄 Extracting PDF: {pdf_path.name}")
        extracted = {"architecture_patterns": [], "video_processing": [], "multimodal_ai": []}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n"
                
                # Determine category based on content
                content_lower = full_text.lower()
                if "multi-modal" in content_lower or "multimodal" in content_lower:
                    category = "multimodal_ai"
                elif "video" in content_lower and "pipeline" in content_lower:
                    category = "video_processing"
                else:
                    category = "architecture_patterns"
                
                # Split into chunks
                chunks = self.text_splitter.split_text(full_text)
                
                for i, chunk in enumerate(chunks):
                    # Skip very short chunks
                    if len(chunk.strip()) < 100:
                        continue
                    
                    doc = {
                        "source_file": f"research/{pdf_path.name}",
                        "source_type": "pdf",
                        "category": category,
                        "title": f"{pdf_path.stem} - Section {i+1}",
                        "content": chunk,
                        "importance": 5,  # Research PDFs are high importance
                        "tags": [category, "research", "nvidia", pdf_path.stem.lower()]
                    }
                    extracted[category].append(doc)
                    
                    if self.use_embeddings and category in self.collections:
                        self._add_to_chromadb(doc, category)
                
                print(f"  ✓ Extracted {sum(len(v) for v in extracted.values())} chunks")
                
        except Exception as e:
            print(f"  ❌ Error processing PDF: {e}")
        
        return extracted
    
    async def extract_github_repository(self, repo_url: str, focus_paths: List[str] = None) -> Dict[str, List[Dict]]:
        """Extract knowledge from GitHub repository"""
        repo_name = repo_url.split('/')[-1]
        print(f"\n🐙 Extracting GitHub repo: {repo_name}")
        extracted = {}
        
        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repository (shallow clone for speed)
                repo_path = Path(temp_dir) / repo_name
                Repo.clone_from(repo_url, repo_path, depth=1)
                print(f"  ✓ Cloned repository")
                
                # Determine repository type and category
                category = self._determine_repo_category(repo_name, repo_path)
                
                # Extract README
                readme_content = self._extract_readme(repo_path)
                if readme_content:
                    doc = {
                        "source_file": f"github/{repo_name}/README.md",
                        "source_type": "github",
                        "category": category,
                        "title": f"{repo_name} - Overview",
                        "content": readme_content,
                        "importance": 4,
                        "tags": [category, "github", repo_name.lower(), "documentation"]
                    }
                    extracted.setdefault(category, []).append(doc)
                    
                    if self.use_embeddings and category in self.collections:
                        self._add_to_chromadb(doc, category)
                
                # Extract from specific paths or auto-detect
                if not focus_paths:
                    focus_paths = self._get_default_paths(repo_name)
                
                for path_pattern in focus_paths:
                    extracted_files = self._extract_from_path(repo_path, path_pattern, repo_name, category)
                    for cat, docs in extracted_files.items():
                        extracted.setdefault(cat, []).extend(docs)
                
                print(f"  ✓ Extracted {sum(len(v) for v in extracted.values())} documents")
                
            except Exception as e:
                print(f"  ❌ Error processing repository: {e}")
        
        return extracted
    
    def _determine_repo_category(self, repo_name: str, repo_path: Path) -> str:
        """Determine the category for a repository"""
        name_lower = repo_name.lower()
        
        # Check by repo name
        if "video" in name_lower or "vision" in name_lower:
            return "video_processing"
        elif "rag" in name_lower:
            return "architecture_patterns"
        elif "llm" in name_lower or "ai-virtual" in name_lower:
            return "multimodal_ai"
        elif "data-flywheel" in name_lower or "router" in name_lower:
            return "production_patterns"
        
        # Check README content
        readme_path = repo_path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8', errors='ignore').lower()
            if "video" in content and "processing" in content:
                return "video_processing"
            elif "deployment" in content or "production" in content:
                return "production_patterns"
        
        return "implementation_patterns"
    
    def _extract_readme(self, repo_path: Path) -> Optional[str]:
        """Extract README content"""
        for readme_name in ["README.md", "readme.md", "Readme.md", "README.rst", "README.txt"]:
            readme_path = repo_path / readme_name
            if readme_path.exists():
                return readme_path.read_text(encoding='utf-8', errors='ignore')
        return None
    
    def _get_default_paths(self, repo_name: str) -> List[str]:
        """Get default paths to extract based on repo type"""
        if "blueprint" in repo_name.lower():
            return ["README.md", "docs/**/*.md", "src/**/*.py", "examples/**/*.py", "*.yaml"]
        else:
            return ["README.md", "docs/**/*.md", "examples/**/*", "src/**/*.py"]
    
    def _extract_from_path(self, repo_path: Path, path_pattern: str, repo_name: str, category: str) -> Dict[str, List[Dict]]:
        """Extract content from specific path pattern"""
        extracted = {}
        
        # Handle glob patterns
        if '*' in path_pattern:
            files = list(repo_path.glob(path_pattern))
        else:
            files = [repo_path / path_pattern] if (repo_path / path_pattern).exists() else []
        
        for file_path in files:
            if file_path.is_file() and file_path.stat().st_size < 1_000_000:  # Skip files > 1MB
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Skip if too short or likely binary
                    if len(content) < 50 or '\0' in content:
                        continue
                    
                    # Determine if code or documentation
                    is_code = file_path.suffix in ['.py', '.js', '.java', '.cpp', '.go', '.rs']
                    splitter = self.code_splitter if is_code else self.text_splitter
                    
                    # Split content
                    chunks = splitter.split_text(content)
                    
                    for i, chunk in enumerate(chunks[:5]):  # Limit chunks per file
                        doc = {
                            "source_file": f"github/{repo_name}/{file_path.relative_to(repo_path)}",
                            "source_type": "github",
                            "category": category,
                            "title": f"{repo_name} - {file_path.stem}" + (f" Part {i+1}" if len(chunks) > 1 else ""),
                            "content": chunk,
                            "importance": 3,
                            "tags": [category, "github", repo_name.lower(), file_path.suffix[1:] if file_path.suffix else "text"]
                        }
                        extracted.setdefault(category, []).append(doc)
                        
                        if self.use_embeddings and category in self.collections:
                            self._add_to_chromadb(doc, category)
                
                except Exception as e:
                    continue  # Skip problematic files
        
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
                    source_repo=item.get("source_type", "unknown"),
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
    print("🚀 Enhanced Knowledge Base Population\n")
    
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
        old_repo_path="Enhanced extraction",
        pdf_dir="research/",
        started_at=datetime.now()
    )
    await report.insert()
    
    # Initialize extractor
    extractor = EnhancedKnowledgeExtractor(use_embeddings=use_embeddings)
    
    all_extracted = {}
    
    try:
        # 1. Extract PDFs from research directory
        research_path = project_root / "research"
        if research_path.exists():
            for pdf_file in research_path.glob("*.pdf"):
                pdf_extracted = await extractor.extract_pdf_knowledge(pdf_file)
                for category, items in pdf_extracted.items():
                    all_extracted.setdefault(category, []).extend(items)
        
        # 2. Extract NVIDIA Blueprint repositories
        nvidia_repos = [
            "https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization",
            "https://github.com/NVIDIA-AI-Blueprints/digital-human",
            "https://github.com/NVIDIA-AI-Blueprints/rag",
            "https://github.com/NVIDIA-AI-Blueprints/ai-virtual-assistant",
            "https://github.com/NVIDIA-AI-Blueprints/data-flywheel",
            "https://github.com/NVIDIA-AI-Blueprints/llm-router"
        ]
        
        for repo_url in nvidia_repos:
            repo_extracted = await extractor.extract_github_repository(repo_url)
            for category, items in repo_extracted.items():
                all_extracted.setdefault(category, []).extend(items)
        
        # Store in MongoDB
        stored_count = await store_in_mongodb(all_extracted, report)
        
        # Update report
        report.statistics = {
            "categories_populated": list(all_extracted.keys()),
            "items_by_category": {k: len(v) for k, v in all_extracted.items()},
            "total_items": sum(len(v) for v in all_extracted.values()),
            "total_stored": stored_count,
            "embeddings_generated": use_embeddings,
            "sources": ["PDFs", "NVIDIA Blueprints"]
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
    
    print("\n✨ Enhanced knowledge base population complete!")
    
    # Repository suggestions analysis
    print("\n📚 Repository Suggestions Analysis:")
    print("\nNVIDIA Blueprints (loaded):")
    print("- video-search-and-summarization: Core reference, directly applicable")
    print("- rag: RAG patterns essential for conversational AI")
    print("- digital-human: Multi-modal interaction patterns")
    print("- ai-virtual-assistant: Conversation flow and context management")
    print("- data-flywheel: Continuous improvement patterns")
    print("- llm-router: Model selection optimization")
    
    print("\nSuggested Additional Repositories:")
    print("\n🎥 Video Processing:")
    print("- ultralytics/ultralytics (2024): YOLO v8 for object tracking")
    print("- PyAV-Org/PyAV (2024): Modern FFmpeg Python bindings")
    print("- Zulko/moviepy (2023): High-level video editing")
    print("\n🤖 Multi-modal AI:")
    print("- mlfoundations/open_clip (2024): SOTA vision-language models")
    print("- haotian-liu/LLaVA (2024): Visual instruction tuning")
    print("- salesforce/LAVIS (2023): Unified vision-language")
    print("\n🔧 Production:")
    print("- langchain-ai/langchain (2024): RAG orchestration")
    print("- chroma-core/chroma (2024): Vector DB patterns")
    print("- celery/celery (2024): Task queue patterns")


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import PyPDF2
        import git
    except ImportError:
        print("Installing required packages...")
        os.system(f"{sys.executable} -m pip install PyPDF2 GitPython")
    
    asyncio.run(main())