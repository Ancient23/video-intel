# Development Knowledge Base Setup

## Overview

Build a RAG-powered development knowledge base that captures all lessons learned, architectural decisions, and implementation patterns from the VideoCommentator project. This serves as both a development tool and a proof-of-concept for the video intelligence platform.

## Architecture

```
dev-knowledge-base/
├── ingestion/                  # Scripts to import existing docs
├── knowledge/                  # Processed knowledge artifacts
│   ├── embeddings/            # Vector embeddings
│   ├── graphs/                # Knowledge graphs
│   └── summaries/             # Document summaries
├── mongodb/                   # Database schemas
├── rag/                       # RAG implementation
├── docs/                      # Source documentation
│   ├── imported/              # From old project
│   ├── pdfs/                  # NVIDIA blueprints
│   └── new/                   # New project docs
└── tools/                     # CLI tools for querying
```

## Phase 1: Knowledge Extraction from Old Repository

### 1.1 Document Inventory Script

```python
# ingestion/inventory_old_docs.py
import os
import json
from pathlib import Path
from typing import List, Dict
import frontmatter
import PyPDF2

class DocumentInventory:
    """Inventories all documentation from the old repository"""
    
    def __init__(self, old_repo_path: str):
        self.old_repo_path = Path(old_repo_path)
        self.docs_path = self.old_repo_path / "apps" / "web" / "docs"
        
    def scan_documentation(self) -> Dict[str, List[Dict]]:
        """Scan all documentation and categorize by type"""
        inventory = {
            "lessons_learned": [],
            "architectural_decisions": [],
            "implementation_guides": [],
            "api_documentation": [],
            "deployment_scripts": [],
            "configuration_patterns": [],
            "ui_patterns": [],
            "known_issues": []
        }
        
        # Key files to prioritize
        priority_files = [
            "history/lessons-learned.md",
            "reference/architecture.md",
            "reference/api.md",
            "guides/operations/pydantic-v2.md",
            "planning/known-issues.md",
            "reference/design/design-system.md",
            "current/implementation-plan.md"
        ]
        
        # Scan all markdown files
        for md_file in self.docs_path.rglob("*.md"):
            relative_path = md_file.relative_to(self.docs_path)
            
            # Read and parse frontmatter if exists
            with open(md_file, 'r') as f:
                post = frontmatter.load(f)
                
            doc_info = {
                "path": str(relative_path),
                "full_path": str(md_file),
                "title": post.get('title', md_file.stem),
                "content": post.content,
                "metadata": post.metadata,
                "category": self._categorize_document(relative_path),
                "priority": str(relative_path) in priority_files
            }
            
            category = doc_info["category"]
            if category in inventory:
                inventory[category].append(doc_info)
                
        return inventory
    
    def extract_code_patterns(self) -> Dict[str, List[Dict]]:
        """Extract reusable code patterns"""
        patterns = {
            "pydantic_models": [],
            "api_endpoints": [],
            "celery_tasks": [],
            "docker_configs": [],
            "deployment_scripts": []
        }
        
        # Extract from Python files
        backend_path = self.old_repo_path / "services" / "backend"
        
        # Pydantic models
        for py_file in backend_path.rglob("*.py"):
            content = py_file.read_text()
            if "BaseModel" in content or "pydantic" in content:
                patterns["pydantic_models"].append({
                    "file": str(py_file.relative_to(self.old_repo_path)),
                    "content": content
                })
        
        # Deployment scripts
        for script in self.old_repo_path.rglob("deploy*.sh"):
            patterns["deployment_scripts"].append({
                "file": str(script.relative_to(self.old_repo_path)),
                "content": script.read_text()
            })
            
        return patterns
```

### 1.2 Knowledge Extraction Pipeline

```python
# ingestion/extract_knowledge.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import UnstructuredMarkdownLoader
import chromadb

class KnowledgeExtractor:
    """Extracts and processes knowledge from documents"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = OpenAIEmbeddings()
        self.chroma_client = chromadb.PersistentClient(path="./knowledge/chromadb")
        
    def process_lessons_learned(self, docs: List[Dict]) -> None:
        """Extract key lessons and patterns"""
        collection = self.chroma_client.create_collection(
            name="lessons_learned",
            metadata={"description": "Architectural decisions and lessons"}
        )
        
        for doc in docs:
            # Extract specific patterns
            lessons = self._extract_lessons(doc['content'])
            
            for lesson in lessons:
                # Create embedding and store
                embedding = self.embeddings.embed_query(lesson['text'])
                
                collection.add(
                    embeddings=[embedding],
                    documents=[lesson['text']],
                    metadatas=[{
                        "source": doc['path'],
                        "type": lesson['type'],
                        "importance": lesson['importance']
                    }],
                    ids=[f"{doc['path']}_{lesson['id']}"]
                )
    
    def _extract_lessons(self, content: str) -> List[Dict]:
        """Extract specific lessons from content"""
        lessons = []
        
        # Pattern matching for different lesson types
        patterns = {
            "bug_fix": r"(?:Fixed|Resolved|Solution):\s*(.+?)(?:\n\n|$)",
            "best_practice": r"(?:Best Practice|Always|Should):\s*(.+?)(?:\n\n|$)",
            "warning": r"(?:Warning|Caution|Important):\s*(.+?)(?:\n\n|$)",
            "pattern": r"(?:Pattern|Approach|Strategy):\s*(.+?)(?:\n\n|$)"
        }
        
        # Extract based on patterns
        # ... implementation ...
        
        return lessons
```

## Phase 2: MongoDB Schema for Development

```python
# mongodb/schemas.py
from datetime import datetime
from typing import List, Dict, Optional
from beanie import Document

class ProjectKnowledge(Document):
    """Stores extracted project knowledge"""
    
    source_file: str
    source_repo: str
    category: str  # "lesson", "pattern", "decision", "issue"
    title: str
    content: str
    code_examples: Optional[List[Dict[str, str]]]
    tags: List[str]
    importance: int  # 1-5 scale
    date_extracted: datetime
    embeddings_id: Optional[str]  # Reference to vector DB
    
    class Settings:
        name = "project_knowledge"

class DevelopmentDecision(Document):
    """Tracks architectural and implementation decisions"""
    
    decision_id: str
    title: str
    context: str
    decision: str
    rationale: str
    alternatives_considered: List[str]
    consequences: Dict[str, List[str]]  # {"positive": [...], "negative": [...]}
    status: str  # "accepted", "deprecated", "superseded"
    date_made: datetime
    related_files: List[str]
    
    class Settings:
        name = "development_decisions"

class ImplementationPattern(Document):
    """Reusable implementation patterns"""
    
    pattern_name: str
    category: str  # "api", "database", "frontend", "deployment"
    description: str
    use_cases: List[str]
    implementation: str  # Code example
    pitfalls: List[str]
    related_patterns: List[str]
    source_files: List[str]
    
    class Settings:
        name = "implementation_patterns"

class ProjectStatus(Document):
    """Current project implementation status"""
    
    component: str
    status: str  # "planned", "in_progress", "completed", "blocked"
    progress_percentage: int
    blockers: List[str]
    dependencies: List[str]
    estimated_completion: Optional[datetime]
    actual_completion: Optional[datetime]
    notes: str
    
    class Settings:
        name = "project_status"
```

## Phase 3: Import Critical Knowledge

### 3.1 Priority Import List

```python
# ingestion/priority_imports.py

CRITICAL_IMPORTS = {
    "pydantic_patterns": {
        "source": "apps/web/docs/guides/operations/pydantic-v2.md",
        "extract": [
            "Field validator patterns",
            "Model configuration",
            "Serialization patterns",
            "Type hints requirements"
        ]
    },
    "architecture_decisions": {
        "source": "apps/web/docs/reference/architecture.md",
        "extract": [
            "Service separation (API/Worker)",
            "Provider abstraction pattern",
            "Caching strategy",
            "State management"
        ]
    },
    "deployment_patterns": {
        "sources": [
            ".github/workflows/deploy_backend.yml",
            "aws-task-definition-*.json",
            "docker-compose.yml"
        ],
        "extract": [
            "ECS deployment configuration",
            "Environment variables",
            "Resource limits",
            "Health checks"
        ]
    },
    "api_patterns": {
        "source": "apps/web/docs/reference/api.md",
        "extract": [
            "Endpoint structure",
            "Response formats",
            "Error handling",
            "Authentication patterns"
        ]
    },
    "known_issues": {
        "source": "apps/web/docs/planning/known-issues.md",
        "extract": [
            "Memory limitations",
            "Provider quirks",
            "Performance bottlenecks"
        ]
    },
    "testing_patterns": {
        "sources": [
            "services/backend/tests/",
            "scripts/README-UI-TESTING.md"
        ],
        "extract": [
            "Test structure",
            "Mocking strategies",
            "UI testing approach"
        ]
    }
}
```

### 3.2 PDF Knowledge Extraction

```python
# ingestion/pdf_extractor.py
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFKnowledgeExtractor:
    """Extract knowledge from NVIDIA Blueprint PDFs"""
    
    def extract_nvidia_patterns(self, pdf_paths: List[str]) -> Dict:
        """Extract architectural patterns from NVIDIA docs"""
        
        patterns = {
            "video_pipeline": [],
            "rag_implementation": [],
            "graph_construction": [],
            "deployment_options": []
        }
        
        for pdf_path in pdf_paths:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            # Extract specific sections
            for page in pages:
                content = page.page_content
                
                # Extract pipeline patterns
                if "pipeline" in content.lower():
                    patterns["video_pipeline"].append({
                        "source": pdf_path,
                        "page": page.metadata.get('page', 0),
                        "content": self._extract_section(content, "pipeline")
                    })
                
                # Extract RAG patterns
                if "retrieval" in content.lower() or "rag" in content.lower():
                    patterns["rag_implementation"].append({
                        "source": pdf_path,
                        "page": page.metadata.get('page', 0),
                        "content": self._extract_section(content, "retrieval")
                    })
                    
        return patterns
```

## Phase 4: Development RAG System

### 4.1 Knowledge Query Interface

```python
# rag/dev_assistant.py
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

class DevelopmentAssistant:
    """RAG-powered development assistant"""
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
    def query_patterns(self, query: str, category: Optional[str] = None) -> str:
        """Query implementation patterns"""
        
        # Search in vector DB
        results = self._search_patterns(query, category)
        
        # Generate response with context
        prompt = f"""
        Based on the VideoCommentator project patterns and the new architecture,
        provide guidance for: {query}
        
        Relevant patterns found:
        {results}
        
        Consider:
        1. Lessons learned from the old implementation
        2. New architectural requirements
        3. Best practices identified
        """
        
        return self.llm.predict(prompt)
    
    def suggest_implementation(self, component: str) -> Dict:
        """Suggest implementation based on past patterns"""
        
        # Find similar components
        similar = self._find_similar_components(component)
        
        # Extract patterns
        patterns = self._extract_implementation_patterns(similar)
        
        return {
            "suggested_structure": patterns.get("structure"),
            "required_patterns": patterns.get("must_have"),
            "common_pitfalls": patterns.get("pitfalls"),
            "reference_implementations": patterns.get("references")
        }
```

### 4.2 CLI Tool for Development

```python
# tools/dev_cli.py
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    """Development knowledge base CLI"""
    pass

@cli.command()
@click.argument('query')
def ask(query):
    """Query the development knowledge base"""
    assistant = DevelopmentAssistant()
    response = assistant.query_patterns(query)
    console.print(response)

@cli.command()
@click.argument('component')
def suggest(component):
    """Get implementation suggestions for a component"""
    assistant = DevelopmentAssistant()
    suggestions = assistant.suggest_implementation(component)
    
    # Display as table
    table = Table(title=f"Implementation Suggestions for {component}")
    table.add_column("Aspect", style="cyan")
    table.add_column("Details", style="green")
    
    for key, value in suggestions.items():
        table.add_row(key, str(value))
    
    console.print(table)

@cli.command()
def status():
    """Show project implementation status"""
    # Query MongoDB for status
    # Display progress dashboard
    pass
```

## Phase 5: Integration with Claude CLI

### 5.1 Context Generation Script

```python
# tools/generate_claude_context.py

class ClaudeContextGenerator:
    """Generates context files for Claude CLI"""
    
    def generate_context(self, topic: str) -> str:
        """Generate context for a specific topic"""
        
        # Query knowledge base
        patterns = self.kb.query_patterns(topic)
        decisions = self.kb.query_decisions(topic)
        issues = self.kb.query_known_issues(topic)
        
        context = f"""
# Context for: {topic}

## Relevant Patterns from VideoCommentator
{patterns}

## Architectural Decisions
{decisions}

## Known Issues to Avoid
{issues}

## Implementation Guidelines
- Always use Pydantic V2 patterns
- Follow the provider abstraction pattern
- Include proper error handling and retries
- Use structured logging with contextual information
- Cache expensive operations with proper TTLs
"""
        
        return context
    
    def update_claude_instructions(self):
        """Update CLAUDE_INSTRUCTIONS.md with latest knowledge"""
        
        # Load current instructions
        # Append learned patterns
        # Save updated version
        pass
```

### 5.2 Knowledge Base Population Script

```python
# scripts/populate_knowledge_base.py
#!/usr/bin/env python3

import asyncio
from pathlib import Path

async def populate_knowledge_base(old_repo_path: str, pdf_dir: str):
    """Main script to populate the development knowledge base"""
    
    # Step 1: Inventory old repository
    inventory = DocumentInventory(old_repo_path)
    docs = inventory.scan_documentation()
    patterns = inventory.extract_code_patterns()
    
    # Step 2: Process PDFs
    pdf_extractor = PDFKnowledgeExtractor()
    nvidia_patterns = pdf_extractor.extract_nvidia_patterns(
        list(Path(pdf_dir).glob("*.pdf"))
    )
    
    # Step 3: Extract and store knowledge
    extractor = KnowledgeExtractor()
    
    # Process each category
    for category, documents in docs.items():
        print(f"Processing {category}: {len(documents)} documents")
        extractor.process_category(category, documents)
    
    # Step 4: Store in MongoDB
    await store_in_mongodb(docs, patterns, nvidia_patterns)
    
    # Step 5: Generate initial context files
    generator = ClaudeContextGenerator()
    generator.update_claude_instructions()
    
    print("Knowledge base population complete!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: populate_knowledge_base.py <old_repo_path> <pdf_dir>")
        sys.exit(1)
    
    asyncio.run(populate_knowledge_base(sys.argv[1], sys.argv[2]))
```

## Usage Workflow

1. **Initial Setup:**
```bash
# Create knowledge base structure
mkdir -p dev-knowledge-base/{ingestion,knowledge,mongodb,rag,docs,tools}

# Install dependencies
pip install langchain chromadb beanie motor click rich PyPDF2 frontmatter

# Set up MongoDB
docker run -d -p 27017:27017 --name devdb mongo

# Initialize the knowledge base
python scripts/populate_knowledge_base.py /path/to/video-commentator ./pdfs
```

2. **Query During Development:**
```bash
# Ask about patterns
./dev-cli ask "How should I implement provider abstraction?"

# Get suggestions
./dev-cli suggest "video_chunking_service"

# Check status
./dev-cli status
```

3. **Use with Claude CLI:**
```bash
# Generate context for specific work
python tools/generate_claude_context.py "mongodb_integration" > .claude/mongodb_context.md

# Use in Claude CLI
claude "Implement MongoDB models following the patterns in .claude/mongodb_context.md"
```

## Benefits

1. **Preserves Institutional Knowledge**: All lessons learned are searchable
2. **Accelerates Development**: Quick access to proven patterns
3. **Prevents Repeated Mistakes**: Known issues are highlighted
4. **Maintains Consistency**: Enforces established patterns
5. **Living Documentation**: Updates as project evolves
6. **Proof of Concept**: Demonstrates the platform's capabilities

This approach turns your development process into a knowledge-driven system that gets smarter over time!