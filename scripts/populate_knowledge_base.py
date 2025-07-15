#!/usr/bin/env python3
import asyncio
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import motor.motor_asyncio
from beanie import init_beanie, Document
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from absolute path
sys.path.insert(0, str(project_root / "dev-knowledge-base"))
from ingestion.inventory_old_docs import DocumentInventory
from ingestion.extract_knowledge import KnowledgeExtractor
from ingestion.pdf_extractor import PDFKnowledgeExtractor


# MongoDB Models
class ProjectKnowledge(Document):
    """Stores extracted project knowledge"""
    
    source_file: str
    source_repo: str
    category: str  # "lesson", "pattern", "decision", "issue"
    title: str
    content: str
    code_examples: list[Dict[str, str]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    importance: int = Field(default=3, ge=1, le=5)  # 1-5 scale
    date_extracted: datetime = Field(default_factory=datetime.now)
    embeddings_id: str = Field(default="")  # Reference to vector DB
    
    class Settings:
        name = "project_knowledge"


class ExtractionReport(Document):
    """Stores extraction run reports"""
    
    extraction_id: str
    old_repo_path: str
    pdf_dir: str
    started_at: datetime
    completed_at: Optional[datetime] = Field(default=None)
    status: str = Field(default="in_progress")  # in_progress, completed, failed
    statistics: Dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    
    class Settings:
        name = "extraction_reports"


async def init_mongodb():
    """Initialize MongoDB connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    
    # Initialize Beanie
    await init_beanie(
        database=client.dev_knowledge_base,
        document_models=[ProjectKnowledge, ExtractionReport]
    )
    
    return client


async def store_inventory_in_mongodb(inventory: Dict, patterns: Dict, report: ExtractionReport):
    """Store document inventory and patterns in MongoDB"""
    stored_count = 0
    
    # Store documentation inventory
    for category, docs in inventory.items():
        for doc in docs:
            try:
                knowledge = ProjectKnowledge(
                    source_file=doc['path'],
                    source_repo=doc.get('full_path', ''),
                    category=category,
                    title=doc.get('title', ''),
                    content=doc.get('content', '')[:5000],  # Limit content size
                    tags=[category, "documentation"],
                    importance=5 if doc.get('priority', False) else 3,
                    date_extracted=datetime.now()
                )
                await knowledge.insert()
                stored_count += 1
            except Exception as e:
                report.errors.append(f"Error storing {doc['path']}: {str(e)}")
    
    # Store code patterns
    for pattern_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            try:
                knowledge = ProjectKnowledge(
                    source_file=pattern['file'],
                    source_repo=pattern['file'],
                    category="pattern",
                    title=f"{pattern_type} pattern",
                    content=pattern.get('content', '')[:5000],
                    code_examples=[{"type": pattern_type, "content": pattern.get('content', '')}],
                    tags=[pattern_type, "code_pattern"],
                    importance=4,
                    date_extracted=datetime.now()
                )
                await knowledge.insert()
                stored_count += 1
            except Exception as e:
                report.errors.append(f"Error storing pattern from {pattern['file']}: {str(e)}")
    
    return stored_count


async def main(old_repo_path: str, pdf_dir: str):
    print(f"📚 Populating knowledge base from: {old_repo_path}")
    print(f"📄 PDFs directory: {pdf_dir}")
    
    # Load environment variables from .env file
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables from .env file")
    
    # Initialize MongoDB
    try:
        await init_mongodb()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("Make sure MongoDB is running (docker compose up -d)")
        return
    
    # Create extraction report
    report = ExtractionReport(
        extraction_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        old_repo_path=old_repo_path,
        pdf_dir=pdf_dir,
        started_at=datetime.now()
    )
    await report.insert()
    
    try:
        # Check if OpenAI API key is set
        openai_key = os.getenv("OPENAI_API_KEY", "")
        use_embeddings = openai_key and openai_key != "your-api-key"
        
        if not use_embeddings:
            print("\n⚠️  Warning: No valid OpenAI API key found. Skipping embeddings generation.")
            print("To enable embeddings, set OPENAI_API_KEY environment variable.")
        
        # Step 1: Inventory old repository
        print("\n📋 Step 1: Inventorying old repository...")
        inventory = DocumentInventory(old_repo_path)
        docs = inventory.scan_documentation()
        patterns = inventory.extract_code_patterns()
        configs = inventory.extract_configuration_patterns()
        
        # Generate inventory report
        inventory_report = inventory.generate_inventory_report(docs)
        print(f"  Found {inventory_report['total_documents']} documents across {len(inventory_report['categories'])} categories")
        
        # Step 2: Process PDFs
        print("\n📄 Step 2: Processing PDF documents...")
        pdf_extractor = PDFKnowledgeExtractor(use_embeddings=use_embeddings)
        pdf_results = pdf_extractor.extract_all_pdfs(pdf_dir)
        
        if pdf_results:
            print(f"  Processed {pdf_results['summary']['total_pdfs']} PDFs")
            for category, count in pdf_results['summary']['patterns_extracted'].items():
                print(f"    - {category}: {count} patterns")
        
        # Step 3: Extract and store knowledge
        print("\n🧠 Step 3: Extracting and storing knowledge...")
        extractor = KnowledgeExtractor(use_embeddings=use_embeddings)
        
        extraction_results = {}
        for category, documents in docs.items():
            if documents:
                print(f"  Processing {category}: {len(documents)} documents")
                result = extractor.process_category(category, documents)
                extraction_results[category] = result
        
        # Step 4: Store in MongoDB
        print("\n💾 Step 4: Storing in MongoDB...")
        stored_count = await store_inventory_in_mongodb(docs, patterns, report)
        print(f"  Stored {stored_count} knowledge items in MongoDB")
        
        # Update report with statistics
        report.statistics = {
            "inventory_report": inventory_report,
            "extraction_results": extraction_results,
            "pdf_summary": pdf_results.get('summary', {}) if pdf_results else {},
            "total_stored": stored_count,
            "patterns_found": {k: len(v) for k, v in patterns.items()},
            "configs_found": {k: len(v) for k, v in configs.items()}
        }
        report.status = "completed"
        report.completed_at = datetime.now()
        
        # Save final results
        results_dir = Path("dev-knowledge-base/knowledge/reports")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save inventory report
        with open(results_dir / f"inventory_report_{report.extraction_id}.json", "w") as f:
            json.dump(inventory_report, f, indent=2)
        
        # Save extraction summary
        with open(results_dir / f"extraction_summary_{report.extraction_id}.json", "w") as f:
            json.dump({
                "extraction_id": report.extraction_id,
                "statistics": report.statistics,
                "completed_at": report.completed_at.isoformat() if report.completed_at else None
            }, f, indent=2)
        
        print(f"\n📊 Summary:")
        print(f"  - Total documents processed: {inventory_report['total_documents']}")
        print(f"  - Knowledge items stored: {stored_count}")
        print(f"  - Priority documents: {len(inventory_report['priority_documents'])}")
        print(f"  - Extraction errors: {len(report.errors)}")
        
        if report.errors:
            print("\n⚠️  Errors encountered:")
            for error in report.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(report.errors) > 5:
                print(f"  ... and {len(report.errors) - 5} more errors")
        
    except Exception as e:
        report.status = "failed"
        report.errors.append(f"Fatal error: {str(e)}")
        print(f"\n❌ Fatal error during extraction: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Save the report
        await report.save()
    
    print("\n✅ Knowledge base population complete!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: populate_knowledge_base.py <old_repo_path> <pdf_dir>")
        sys.exit(1)
    
    asyncio.run(main(sys.argv[1], sys.argv[2]))
