#!/usr/bin/env python3
"""Add additional high-priority repositories to knowledge base"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import motor.motor_asyncio
from beanie import init_beanie
from dotenv import load_dotenv

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dev-knowledge-base"))

# Import models and enhanced extractor
from models import ProjectKnowledge, ExtractionReport
from populate_enhanced_knowledge_base import EnhancedKnowledgeExtractor, store_in_mongodb


async def main():
    """Main function to add additional repositories"""
    print("🚀 Adding High-Priority Repositories to Knowledge Base\n")
    
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
        old_repo_path="Additional high-priority repos",
        pdf_dir="N/A",
        started_at=datetime.now()
    )
    await report.insert()
    
    # Initialize extractor
    extractor = EnhancedKnowledgeExtractor(use_embeddings=use_embeddings)
    
    all_extracted = {}
    
    # High-priority repositories with custom focus paths
    repos_config = [
        {
            "url": "https://github.com/mlfoundations/open_clip",
            "focus_paths": ["README.md", "docs/**/*.md", "src/open_clip/**/*.py", "tutorials/**/*"],
            "description": "State-of-the-art vision-language models"
        },
        {
            "url": "https://github.com/haotian-liu/LLaVA",
            "focus_paths": ["README.md", "docs/**/*.md", "llava/**/*.py", "docs/MODEL_ZOO.md"],
            "description": "Visual instruction tuning for video understanding"
        },
        {
            "url": "https://github.com/ultralytics/ultralytics",
            "focus_paths": ["README.md", "docs/**/*.md", "ultralytics/models/**/*.py", "examples/**/*.py"],
            "description": "YOLOv8 for object detection and tracking"
        },
        {
            "url": "https://github.com/langchain-ai/langchain",
            "focus_paths": ["README.md", "docs/**/*.md", "libs/langchain/langchain/chains/**/*.py", 
                          "cookbook/**/*.ipynb", "libs/langchain/langchain/memory/**/*.py"],
            "description": "RAG orchestration and conversation patterns"
        },
        {
            "url": "https://github.com/chroma-core/chroma",
            "focus_paths": ["README.md", "docs/**/*.md", "chromadb/**/*.py", "examples/**/*"],
            "description": "Vector database patterns and best practices"
        },
        {
            "url": "https://github.com/PyAV-Org/PyAV",
            "focus_paths": ["README.md", "docs/**/*.rst", "av/**/*.pyx", "examples/**/*.py"],
            "description": "Pythonic FFmpeg bindings for video processing"
        }
    ]
    
    try:
        for repo_config in repos_config:
            print(f"\n📦 Processing: {repo_config['description']}")
            repo_extracted = await extractor.extract_github_repository(
                repo_config["url"],
                repo_config.get("focus_paths")
            )
            for category, items in repo_extracted.items():
                all_extracted.setdefault(category, []).extend(items)
        
        # Store in MongoDB
        stored_count = await store_in_mongodb(all_extracted, report)
        
        # Update report
        report.statistics = {
            "repositories_processed": len(repos_config),
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
        print(f"  - Repositories processed: {len(repos_config)}")
        print(f"  - Total items extracted: {sum(len(v) for v in all_extracted.values())}")
        print(f"  - Items stored in MongoDB: {stored_count}")
        
        print("\n📈 Items by category:")
        for category, items in sorted(all_extracted.items()):
            print(f"  - {category}: {len(items)} items")
        
        print("\n✅ Repository additions complete!")
        print("\n🎯 How these repos help the Video Intelligence Platform:")
        print("\n1. **open_clip**: Essential for video-text similarity search")
        print("   - Use for: Embedding video frames and text queries")
        print("   - Better than OpenAI CLIP: More models, better performance")
        
        print("\n2. **LLaVA**: Visual understanding with language models")
        print("   - Use for: Generating detailed video descriptions")
        print("   - Understands complex visual scenes and actions")
        
        print("\n3. **ultralytics (YOLOv8)**: Fast object detection")
        print("   - Use for: Tracking objects/people across video")
        print("   - Real-time performance, excellent accuracy")
        
        print("\n4. **langchain**: RAG orchestration")
        print("   - Use for: Conversation memory, retrieval chains")
        print("   - Integrates with our ChromaDB vector store")
        
        print("\n5. **chroma**: Vector database expertise")
        print("   - Use for: Optimizing our current ChromaDB usage")
        print("   - Performance tuning, best practices")
        
        print("\n6. **PyAV**: Professional video processing")
        print("   - Use for: Frame extraction, video manipulation")
        print("   - More control than moviepy, production-ready")
        
    except Exception as e:
        report.status = "failed"
        report.errors.append(f"Fatal error: {str(e)}")
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await report.save()


if __name__ == "__main__":
    asyncio.run(main())