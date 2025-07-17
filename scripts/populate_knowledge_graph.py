#!/usr/bin/env python3
"""
Unified knowledge base population script with Qdrant and Neo4j Graph-RAG support.

This script populates the development knowledge base from multiple sources:
- PDF research documents
- GitHub repositories
- Internal project documentation
- Curated resources
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dev-knowledge-base"))

# Third-party imports
from dotenv import load_dotenv
import motor.motor_asyncio
from beanie import init_beanie
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from py2neo import Graph, Node, Relationship
import PyPDF2
import aiohttp
import aiofiles
from git import Repo

# Local imports
from models import ProjectKnowledge, ExtractionReport, SourceType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()


class UnifiedKnowledgePopulator:
    """Unified knowledge base populator with Graph-RAG support"""
    
    def __init__(self):
        # Vector DB (Qdrant)
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")
        self.qdrant_client = None
        
        # Graph DB (Neo4j)
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
        self.neo4j_graph = None
        
        # OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # MongoDB
        self.db = None
        
        # Statistics
        self.stats = {
            "total_documents": 0,
            "pdfs_processed": 0,
            "github_repos_processed": 0,
            "internal_docs_processed": 0,
            "entities_extracted": 0,
            "relationships_created": 0,
            "errors": []
        }
    
    async def initialize(self):
        """Initialize all connections"""
        # MongoDB
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/video-intelligence")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db_name = mongo_url.split("/")[-1].split("?")[0]
        self.db = client[db_name]
        await init_beanie(database=self.db, document_models=[ProjectKnowledge, ExtractionReport])
        
        # Qdrant
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        await self._ensure_qdrant_collection()
        
        # Neo4j
        try:
            self.neo4j_graph = Graph(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            # Create constraints and indexes
            self._setup_neo4j_schema()
            logger.info("✅ Neo4j connected and schema initialized")
        except Exception as e:
            logger.warning(f"⚠️  Neo4j connection failed: {e}. Graph features will be disabled.")
            self.neo4j_graph = None
        
        logger.info("✅ All connections initialized")
    
    async def _ensure_qdrant_collection(self):
        """Ensure Qdrant collection exists"""
        collections = self.qdrant_client.get_collections().collections
        if not any(col.name == self.collection_name for col in collections):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI embedding size
                    distance=Distance.COSINE
                )
            )
            logger.info(f"✅ Created Qdrant collection: {self.collection_name}")
    
    def _setup_neo4j_schema(self):
        """Setup Neo4j schema with constraints and indexes"""
        if not self.neo4j_graph:
            return
            
        try:
            # Create constraints for unique IDs
            self.neo4j_graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.id IS UNIQUE")
            self.neo4j_graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE")
            
            # Create indexes for performance
            self.neo4j_graph.run("CREATE INDEX IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.category)")
            self.neo4j_graph.run("CREATE INDEX IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.source_type)")
            self.neo4j_graph.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)")
            
        except Exception as e:
            logger.warning(f"Neo4j schema setup warning: {e}")
    
    async def populate_all_sources(self):
        """Main entry point to populate from all sources"""
        logger.info("🚀 Starting unified knowledge base population...")
        
        # Create extraction report
        report = ExtractionReport()
        await report.save()
        
        try:
            # Process in order of priority, but for now just test internal docs
            # 3. Process internal documentation
            await self._process_internal_docs()
            
            # TODO: Enable these after testing
            # # 1. Process PDFs
            # await self._process_pdfs()
            
            # # 2. Process GitHub repositories
            # await self._process_github_repos()
            
            # # 4. Process Graph-RAG documentation
            # await self._process_graphrag_docs()
            
            # # 5. Process additional web resources
            # await self._process_web_resources()
            
            # Update report
            report.completed_at = datetime.utcnow()
            report.status = "completed"
            report.statistics = self.stats
            await report.save()
            
            # Print summary
            self._print_summary()
            
        except Exception as e:
            logger.error(f"Population failed: {e}")
            report.status = "failed"
            report.errors.append(str(e))
            await report.save()
            raise
    
    async def _process_pdfs(self):
        """Process PDF research documents"""
        # Check multiple PDF locations
        pdf_dirs = [
            project_root / "dev-knowledge-base" / "docs" / "pdfs",
            project_root / "research",
            project_root / "resources"
        ]
        
        all_pdf_files = []
        for pdf_dir in pdf_dirs:
            if pdf_dir.exists():
                pdf_files = list(pdf_dir.glob("*.pdf"))
                all_pdf_files.extend(pdf_files)
                logger.info(f"Found {len(pdf_files)} PDFs in {pdf_dir}")
        
        logger.info(f"Total PDFs to process: {len(all_pdf_files)}")
        
        for pdf_path in all_pdf_files:
            try:
                await self._process_single_pdf(pdf_path)
                self.stats["pdfs_processed"] += 1
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                self.stats["errors"].append(f"PDF {pdf_path.name}: {str(e)}")
    
    async def _process_single_pdf(self, pdf_path: Path):
        """Process a single PDF file"""
        logger.info(f"📄 Processing PDF: {pdf_path.name}")
        
        # Extract text from PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            # Create knowledge document
            doc = ProjectKnowledge(
                source_file=str(pdf_path.relative_to(project_root)),
                source_repo="video-intelligence-platform",
                source_type=SourceType.PDF,
                category="research",
                title=f"{pdf_path.stem} - Part {i+1}",
                content=chunk,
                importance=4,
                tags=["nvidia", "blueprint", "architecture", "video-ai"]
            )
            
            # Save to MongoDB
            await doc.save()
            
            # Add to Qdrant
            vector_id = await self._add_to_qdrant(doc)
            doc.vector_db_id = vector_id
            await doc.save()
            
            # Extract entities and add to Neo4j
            if self.neo4j_graph:
                graph_id = await self._add_to_neo4j(doc)
                doc.graph_node_id = graph_id
                await doc.save()
            
            self.stats["total_documents"] += 1
    
    async def _process_github_repos(self):
        """Process GitHub repositories"""
        repos = [
            # NVIDIA AI Blueprints (Primary - CRITICAL)
            ("https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization", ["README.md", "docs/**/*", "src/**/*.py", "*.md"], 5),
            ("https://github.com/NVIDIA-AI-Blueprints/digital-human", ["README.md", "avatar/**/*", "chat/**/*", "docs/**/*"], 4),
            ("https://github.com/NVIDIA-AI-Blueprints/data-flywheel", ["README.md", "docs/02-quickstart.md", "nemo/**/*", "optimization/**/*"], 4),
            ("https://github.com/NVIDIA-AI-Blueprints/rag", ["README.md", "src/**/*.py", "docs/**/*.md"], 4),
            
            # Video Processing & ML Libraries
            ("https://github.com/mlfoundations/open_clip", ["README.md", "src/open_clip/**/*.py", "docs/**/*"], 3),
            ("https://github.com/haotian-liu/LLaVA", ["README.md", "llava/**/*.py", "docs/**/*"], 3),
            ("https://github.com/qdrant/qdrant", ["README.md", "lib/collection/**/*", "docs/**/*.md"], 4),
            ("https://github.com/neo4j/neo4j", ["README.md", "community/cypher/**/*", "docs/**/*.md"], 4),
            
            # Infrastructure & Best Practices
            ("https://github.com/celery/celery", ["docs/userguide/canvas.rst", "celery/canvas/**/*.py", "docs/userguide/*.rst"], 4),
            ("https://github.com/boto/boto3", ["boto3/docs/**/*", "examples/**/*.py"], 3),
            ("https://github.com/FFmpeg/FFmpeg", ["doc/ffmpeg.texi", "doc/filters.texi", "doc/examples/**/*"], 3),
            ("https://github.com/tiangolo/fastapi", ["docs/**/*.md", "fastapi/**/*.py"], 3),
            ("https://github.com/encode/httpx", ["docs/**/*.md", "httpx/**/*.py"], 3),
            ("https://github.com/roman-right/beanie", ["docs/**/*.md", "beanie/**/*.py"], 3),
        ]
        
        temp_dir = Path("/tmp/knowledge_repos")
        temp_dir.mkdir(exist_ok=True)
        
        for repo_data in repos:
            try:
                if len(repo_data) == 3:
                    repo_url, patterns, importance = repo_data
                else:
                    repo_url, patterns = repo_data
                    importance = 3  # default importance
                    
                await self._process_single_repo(repo_url, patterns, temp_dir, importance)
                self.stats["github_repos_processed"] += 1
            except Exception as e:
                logger.error(f"Failed to process {repo_url}: {e}")
                self.stats["errors"].append(f"GitHub {repo_url}: {str(e)}")
    
    async def _process_single_repo(self, repo_url: str, patterns: List[str], temp_dir: Path, importance: int = 3):
        """Process a single GitHub repository"""
        repo_name = repo_url.split("/")[-1]
        logger.info(f"🐙 Processing GitHub repo: {repo_name}")
        
        # Clone or update repo
        repo_path = temp_dir / repo_name
        if repo_path.exists():
            repo = Repo(repo_path)
            repo.remotes.origin.pull()
        else:
            repo = Repo.clone_from(repo_url, repo_path)
        
        # Process files matching patterns
        for pattern in patterns:
            for file_path in repo_path.rglob(pattern.replace("**", "*")):
                if file_path.is_file() and file_path.suffix in ['.py', '.md', '.txt']:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        
                        # Skip very large files
                        if len(content) > 100000:
                            continue
                        
                        # Create knowledge document
                        doc = ProjectKnowledge(
                            source_file=str(file_path.relative_to(repo_path)),
                            source_repo=repo_name,
                            source_type=SourceType.GITHUB,
                            category=self._categorize_content(file_path, content),
                            title=f"{repo_name}/{file_path.name}",
                            content=content[:5000],  # Limit content size
                            importance=importance,
                            tags=self._extract_tags(content)
                        )
                        
                        # Save and index
                        await doc.save()
                        
                        # Add to Qdrant
                        vector_id = await self._add_to_qdrant(doc)
                        doc.vector_db_id = vector_id
                        await doc.save()
                        
                        # Add to Neo4j
                        if self.neo4j_graph:
                            graph_id = await self._add_to_neo4j(doc)
                            doc.graph_node_id = graph_id
                            await doc.save()
                        
                        self.stats["total_documents"] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to process {file_path}: {e}")
    
    async def _process_internal_docs(self):
        """Process internal project documentation"""
        docs_to_process = [
            (project_root / "docs" / "new" / "video-intelligence-prd.md", "requirements", 5),
            (project_root / "README.md", "overview", 4),
            (project_root / "CLAUDE.md", "development", 4),
        ]
        
        for doc_path, category, importance in docs_to_process:
            if doc_path.exists():
                try:
                    content = doc_path.read_text()
                    
                    # Split into sections
                    sections = self._split_markdown_sections(content)
                    
                    for section_title, section_content in sections.items():
                        doc = ProjectKnowledge(
                            source_file=str(doc_path.relative_to(project_root)),
                            source_repo="video-intelligence-platform",
                            source_type=SourceType.INTERNAL,
                            category=category,
                            title=f"{doc_path.stem} - {section_title}",
                            content=section_content,
                            importance=importance,
                            tags=["project", "internal", category]
                        )
                        
                        await doc.save()
                        
                        # Index in Qdrant and Neo4j
                        vector_id = await self._add_to_qdrant(doc)
                        doc.vector_db_id = vector_id
                        
                        if self.neo4j_graph:
                            graph_id = await self._add_to_neo4j(doc)
                            doc.graph_node_id = graph_id
                        
                        await doc.save()
                        
                        self.stats["total_documents"] += 1
                        self.stats["internal_docs_processed"] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process {doc_path}: {e}")
                    self.stats["errors"].append(f"Internal {doc_path.name}: {str(e)}")
    
    async def _process_graphrag_docs(self):
        """Process Graph-RAG specific documentation"""
        # Fetch Qdrant Graph-RAG documentation
        graphrag_url = "https://qdrant.tech/documentation/examples/graphrag-qdrant-neo4j/"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(graphrag_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        doc = ProjectKnowledge(
                            source_file=graphrag_url,
                            source_repo="qdrant-docs",
                            source_type=SourceType.DOCUMENTATION,
                            category="graph-rag",
                            title="Graph-RAG with Qdrant and Neo4j",
                            content=content,
                            importance=5,
                            tags=["graph-rag", "qdrant", "neo4j", "architecture"]
                        )
                        
                        await doc.save()
                        
                        # Index
                        vector_id = await self._add_to_qdrant(doc)
                        doc.vector_db_id = vector_id
                        
                        if self.neo4j_graph:
                            graph_id = await self._add_to_neo4j(doc)
                            doc.graph_node_id = graph_id
                        
                        await doc.save()
                        
                        self.stats["total_documents"] += 1
                        logger.info("✅ Processed Graph-RAG documentation")
                        
        except Exception as e:
            logger.error(f"Failed to fetch Graph-RAG docs: {e}")
            self.stats["errors"].append(f"Graph-RAG docs: {str(e)}")
    
    async def _process_web_resources(self):
        """Process additional web documentation resources"""
        web_resources = [
            {
                "url": "https://docs.aws.amazon.com/rekognition/latest/dg/video.html",
                "title": "AWS Rekognition Video Documentation",
                "category": "video_processing",
                "importance": 4,
                "tags": ["aws", "rekognition", "video-analysis", "shot-detection"]
            },
            {
                "url": "https://docs.celeryq.dev/en/stable/userguide/canvas.html",
                "title": "Celery Canvas - Designing Complex Workflows",
                "category": "infrastructure",
                "importance": 4,
                "tags": ["celery", "canvas", "workflow", "distributed-processing"]
            },
            {
                "url": "https://ffmpeg.org/ffmpeg-filters.html",
                "title": "FFmpeg Filters Documentation",
                "category": "video_processing",
                "importance": 3,
                "tags": ["ffmpeg", "video-processing", "filters", "chunking"]
            },
            {
                "url": "https://www.mongodb.com/docs/manual/aggregation/",
                "title": "MongoDB Aggregation Pipeline",
                "category": "data_model",
                "importance": 3,
                "tags": ["mongodb", "aggregation", "pipeline", "query-optimization"]
            },
            {
                "url": "https://redis.io/docs/manual/patterns/",
                "title": "Redis Patterns and Best Practices",
                "category": "infrastructure",
                "importance": 3,
                "tags": ["redis", "caching", "patterns", "performance"]
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for resource in web_resources:
                try:
                    async with session.get(resource["url"], timeout=30) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Clean HTML content (basic cleaning)
                            if "<html" in content.lower():
                                # Simple HTML stripping (in production, use BeautifulSoup)
                                import re
                                content = re.sub(r'<[^>]+>', '', content)
                                content = re.sub(r'\s+', ' ', content)
                            
                            doc = ProjectKnowledge(
                                source_file=resource["url"],
                                source_repo="external-docs",
                                source_type=SourceType.DOCUMENTATION,
                                category=resource["category"],
                                title=resource["title"],
                                content=content[:10000],  # Limit content size
                                importance=resource["importance"],
                                tags=resource["tags"]
                            )
                            
                            await doc.save()
                            
                            # Index
                            vector_id = await self._add_to_qdrant(doc)
                            doc.vector_db_id = vector_id
                            
                            if self.neo4j_graph:
                                graph_id = await self._add_to_neo4j(doc)
                                doc.graph_node_id = graph_id
                            
                            await doc.save()
                            
                            self.stats["total_documents"] += 1
                            logger.info(f"✅ Processed web resource: {resource['title']}")
                            
                except Exception as e:
                    logger.error(f"Failed to fetch {resource['url']}: {e}")
                    self.stats["errors"].append(f"Web resource {resource['title']}: {str(e)}")
    
    async def _add_to_qdrant(self, doc: ProjectKnowledge) -> str:
        """Add document to Qdrant and return vector ID"""
        # Generate embedding
        text = f"{doc.title}\n\n{doc.content}"
        embedding = self.embeddings.embed_query(text)
        
        # Create unique ID
        doc_id = hashlib.md5(f"{doc.source_file}:{doc.title}".encode()).hexdigest()
        
        # Create point
        point = PointStruct(
            id=doc_id,
            vector=embedding,
            payload={
                "text": text,
                "title": doc.title,
                "category": doc.category,
                "source_file": doc.source_file,
                "source_repo": doc.source_repo,
                "source_type": doc.source_type.value,  # Convert enum to string
                "importance": doc.importance,
                "tags": doc.tags,
                "mongodb_id": str(doc.id),
                "created_at": doc.created_at.isoformat()
            }
        )
        
        # Upsert to Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        return doc_id
    
    async def _add_to_neo4j(self, doc: ProjectKnowledge) -> str:
        """Add document to Neo4j and extract entities/relationships"""
        if not self.neo4j_graph:
            return None
        
        try:
            # Create knowledge node
            node_id = hashlib.md5(f"{doc.source_file}:{doc.title}".encode()).hexdigest()
            
            # Create node in Neo4j
            query = """
            MERGE (n:KnowledgeNode {id: $id})
            SET n.title = $title,
                n.category = $category,
                n.source_type = $source_type,
                n.source_file = $source_file,
                n.importance = $importance,
                n.mongodb_id = $mongodb_id,
                n.created_at = $created_at
            RETURN n
            """
            
            self.neo4j_graph.run(query,
                id=node_id,
                title=doc.title,
                category=doc.category,
                source_type=doc.source_type.value,  # Convert enum to string
                source_file=doc.source_file,
                importance=doc.importance,
                mongodb_id=str(doc.id),
                created_at=doc.created_at.isoformat()
            )
            
            # Extract and create entities
            entities = self._extract_entities(doc.content)
            doc.entities = entities
            
            for entity in entities:
                # Create entity node
                entity_query = """
                MERGE (e:Entity {name: $name})
                SET e.type = $type
                RETURN e
                """
                self.neo4j_graph.run(entity_query, name=entity["name"], type=entity["type"])
                
                # Create relationship
                rel_query = """
                MATCH (n:KnowledgeNode {id: $node_id})
                MATCH (e:Entity {name: $entity_name})
                MERGE (n)-[r:MENTIONS]->(e)
                SET r.count = coalesce(r.count, 0) + 1
                """
                self.neo4j_graph.run(rel_query, node_id=node_id, entity_name=entity["name"])
                
                self.stats["entities_extracted"] += 1
            
            # Create relationships between related documents
            await self._create_document_relationships(doc, node_id)
            
            return node_id
            
        except Exception as e:
            logger.warning(f"Neo4j operation failed: {e}")
            return None
    
    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Simple entity extraction (can be enhanced with NLP)"""
        entities = []
        
        # Extract common patterns
        patterns = {
            "technology": [
                "Qdrant", "Neo4j", "MongoDB", "Redis", "FastAPI", "Celery", "Docker", "AWS", "S3", "Rekognition",
                "FFmpeg", "Boto3", "httpx", "Beanie", "Kubernetes", "PostgreSQL", "Elasticsearch", "Kafka",
                "RabbitMQ", "nginx", "Grafana", "Prometheus", "Jenkins", "GitHub Actions"
            ],
            "concept": [
                "RAG", "Graph-RAG", "embeddings", "vector search", "knowledge graph", "semantic search",
                "two-phase pipeline", "ingestion phase", "retrieval phase", "video chunking", "shot detection",
                "scene analysis", "multimodal", "cost optimization", "data flywheel", "inference caching"
            ],
            "framework": [
                "LangChain", "OpenAI", "NVIDIA", "PyTorch", "TensorFlow", "Open CLIP", "LLaVA",
                "NeMo", "Cosmos VLM", "VILA", "GPT-4 Vision", "Claude", "Gemini", "Llama"
            ],
            "service": [
                "AWS Rekognition", "Google Video AI", "Azure Video Analyzer", "OpenAI API",
                "NVIDIA API", "Anthropic API", "Hugging Face", "Pinecone", "Weaviate", "Milvus"
            ],
            "pattern": [
                "provider abstraction", "factory pattern", "async/await", "dependency injection",
                "canvas workflow", "error handling", "retry logic", "connection pooling", "batch processing"
            ]
        }
        
        content_lower = content.lower()
        for entity_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    entities.append({"name": keyword, "type": entity_type})
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in entities:
            key = f"{entity['name']}:{entity['type']}"
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    async def _create_document_relationships(self, doc: ProjectKnowledge, node_id: str):
        """Create relationships between related documents"""
        # Find similar documents using Qdrant
        text = f"{doc.title}\n\n{doc.content[:500]}"
        embedding = self.embeddings.embed_query(text)
        
        # Search for similar documents
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=5,
            score_threshold=0.7
        )
        
        for result in results:
            if result.id != doc.vector_db_id:
                # Create similarity relationship
                query = """
                MATCH (n1:KnowledgeNode {id: $node1_id})
                MATCH (n2:KnowledgeNode {id: $node2_id})
                MERGE (n1)-[r:SIMILAR_TO]->(n2)
                SET r.score = $score
                """
                
                try:
                    self.neo4j_graph.run(query,
                        node1_id=node_id,
                        node2_id=result.id,
                        score=result.score
                    )
                    self.stats["relationships_created"] += 1
                except:
                    pass  # Ignore if relationship already exists
    
    def _categorize_content(self, file_path: Path, content: str) -> str:
        """Categorize content based on file path and content"""
        path_str = str(file_path).lower()
        content_lower = content.lower()
        
        if "test" in path_str:
            return "testing"
        elif "doc" in path_str or "readme" in path_str:
            return "documentation"
        elif "api" in path_str or "endpoint" in content_lower:
            return "api"
        elif "model" in path_str or "schema" in path_str:
            return "data_model"
        elif any(x in content_lower for x in ["video", "frame", "shot"]):
            return "video_processing"
        elif any(x in content_lower for x in ["embed", "vector", "similarity"]):
            return "embeddings"
        elif any(x in content_lower for x in ["rag", "retrieval", "search"]):
            return "rag"
        else:
            return "general"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = []
        content_lower = content.lower()
        
        # Technology tags
        tech_keywords = ["python", "javascript", "typescript", "docker", "kubernetes", "aws", "mongodb", "redis", "neo4j", "qdrant"]
        for keyword in tech_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        # Domain tags
        domain_keywords = ["video", "ai", "ml", "nlp", "computer vision", "rag", "graph", "api", "backend", "frontend"]
        for keyword in domain_keywords:
            if keyword in content_lower:
                tags.append(keyword.replace(" ", "-"))
        
        return list(set(tags))[:10]  # Limit to 10 tags
    
    def _split_markdown_sections(self, content: str) -> Dict[str, str]:
        """Split markdown content into sections"""
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        for line in content.split("\n"):
            if line.startswith("# "):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[2:].strip()
                current_content = []
            elif line.startswith("## "):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        return sections
    
    def _print_summary(self):
        """Print population summary"""
        print("\n" + "="*60)
        print("📊 Knowledge Base Population Summary")
        print("="*60)
        print(f"Total documents processed: {self.stats['total_documents']}")
        print(f"PDFs processed: {self.stats['pdfs_processed']}")
        print(f"GitHub repos processed: {self.stats['github_repos_processed']}")
        print(f"Internal docs processed: {self.stats['internal_docs_processed']}")
        
        if self.neo4j_graph:
            print(f"Entities extracted: {self.stats['entities_extracted']}")
            print(f"Relationships created: {self.stats['relationships_created']}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
        
        print("\n✅ Knowledge base population complete!")
        print("="*60)


async def main():
    """Main entry point"""
    populator = UnifiedKnowledgePopulator()
    
    try:
        await populator.initialize()
        await populator.populate_all_sources()
    except Exception as e:
        logger.error(f"Population failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())