import re
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings
import hashlib


class PDFKnowledgeExtractor:
    """Extract knowledge from NVIDIA Blueprint PDFs and other technical documentation"""
    
    def __init__(self, chroma_path: str = "./knowledge/chromadb"):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection for PDF knowledge
        try:
            self.pdf_collection = self.chroma_client.get_collection("pdf_knowledge")
        except:
            self.pdf_collection = self.chroma_client.create_collection(
                name="pdf_knowledge",
                metadata={"description": "Knowledge extracted from technical PDFs"}
            )
    
    def extract_nvidia_patterns(self, pdf_paths: List[str]) -> Dict[str, List[Dict]]:
        """Extract architectural patterns from NVIDIA docs"""
        
        patterns = {
            "video_pipeline": [],
            "rag_implementation": [],
            "graph_construction": [],
            "deployment_options": [],
            "performance_optimization": [],
            "multimodal_processing": []
        }
        
        for pdf_path in pdf_paths:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                print(f"Warning: PDF file not found: {pdf_path}")
                continue
                
            try:
                loader = PyPDFLoader(str(pdf_path))
                pages = loader.load()
                
                print(f"Processing PDF: {pdf_path.name} ({len(pages)} pages)")
                
                # Extract specific sections
                for page_num, page in enumerate(pages):
                    content = page.page_content
                    
                    # Extract pipeline patterns
                    if any(keyword in content.lower() for keyword in ["pipeline", "video processing", "ingestion"]):
                        extracted = self._extract_section(content, "pipeline", page_num)
                        if extracted:
                            patterns["video_pipeline"].append({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "content": extracted,
                                "type": "video_pipeline"
                            })
                    
                    # Extract RAG patterns
                    if any(keyword in content.lower() for keyword in ["retrieval", "rag", "vector", "embedding"]):
                        extracted = self._extract_section(content, "retrieval", page_num)
                        if extracted:
                            patterns["rag_implementation"].append({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "content": extracted,
                                "type": "rag_pattern"
                            })
                    
                    # Extract graph construction patterns
                    if any(keyword in content.lower() for keyword in ["graph", "knowledge graph", "neo4j", "relationship"]):
                        extracted = self._extract_section(content, "graph", page_num)
                        if extracted:
                            patterns["graph_construction"].append({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "content": extracted,
                                "type": "graph_pattern"
                            })
                    
                    # Extract deployment patterns
                    if any(keyword in content.lower() for keyword in ["deploy", "kubernetes", "docker", "scale", "production"]):
                        extracted = self._extract_section(content, "deployment", page_num)
                        if extracted:
                            patterns["deployment_options"].append({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "content": extracted,
                                "type": "deployment"
                            })
                    
                    # Extract performance optimization patterns
                    if any(keyword in content.lower() for keyword in ["performance", "optimization", "cache", "speed", "latency"]):
                        extracted = self._extract_section(content, "performance", page_num)
                        if extracted:
                            patterns["performance_optimization"].append({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "content": extracted,
                                "type": "performance"
                            })
                    
                    # Extract multimodal processing patterns
                    if any(keyword in content.lower() for keyword in ["multimodal", "vision", "audio", "speech", "visual"]):
                        extracted = self._extract_section(content, "multimodal", page_num)
                        if extracted:
                            patterns["multimodal_processing"].append({
                                "source": pdf_path.name,
                                "page": page_num + 1,
                                "content": extracted,
                                "type": "multimodal"
                            })
                
                # Store patterns in ChromaDB
                self._store_patterns_in_chroma(patterns, pdf_path.name)
                
            except Exception as e:
                print(f"Error processing PDF {pdf_path}: {e}")
                continue
                
        return patterns
    
    def extract_all_pdfs(self, pdf_directory: str) -> Dict[str, Any]:
        """Extract knowledge from all PDFs in a directory"""
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            print(f"Warning: PDF directory not found: {pdf_dir}")
            return {}
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to process")
        
        all_patterns = self.extract_nvidia_patterns([str(f) for f in pdf_files])
        
        # Generate summary statistics
        summary = {
            "total_pdfs": len(pdf_files),
            "patterns_extracted": {
                category: len(patterns) for category, patterns in all_patterns.items()
            },
            "processed_files": [f.name for f in pdf_files],
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        return {
            "patterns": all_patterns,
            "summary": summary
        }
    
    def extract_specific_topics(self, pdf_path: str, topics: List[str]) -> Dict[str, List[Dict]]:
        """Extract specific topics from a PDF"""
        results = {topic: [] for topic in topics}
        
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            for page_num, page in enumerate(pages):
                content = page.page_content
                
                for topic in topics:
                    if topic.lower() in content.lower():
                        # Extract surrounding context
                        extracted = self._extract_topic_context(content, topic, page_num)
                        if extracted:
                            results[topic].append({
                                "source": Path(pdf_path).name,
                                "page": page_num + 1,
                                "content": extracted,
                                "topic": topic
                            })
            
            # Store in ChromaDB
            self._store_topic_extracts_in_chroma(results, Path(pdf_path).name)
            
        except Exception as e:
            print(f"Error extracting topics from {pdf_path}: {e}")
            
        return results
    
    def _extract_section(self, content: str, section_type: str, page_num: int) -> Optional[str]:
        """Extract relevant section based on type"""
        
        # Define patterns for different section types
        section_patterns = {
            "pipeline": [
                r"(?:Video|Processing|Ingestion)\s+Pipeline[\s\S]{0,1000}",
                r"Pipeline\s+(?:Architecture|Design|Components)[\s\S]{0,1000}",
                r"(?:Step|Stage)\s+\d+:[\s\S]{0,1000}"
            ],
            "retrieval": [
                r"(?:RAG|Retrieval)(?:\s+\w+){0,3}[\s\S]{0,1000}",
                r"(?:Vector|Embedding)(?:\s+\w+){0,3}[\s\S]{0,1000}",
                r"(?:Semantic|Similarity)\s+Search[\s\S]{0,1000}"
            ],
            "graph": [
                r"(?:Knowledge|Scene)\s+Graph[\s\S]{0,1000}",
                r"(?:Node|Edge|Relationship)(?:\s+\w+){0,3}[\s\S]{0,1000}",
                r"Graph\s+(?:Construction|Building|Creation)[\s\S]{0,1000}"
            ],
            "deployment": [
                r"(?:Deploy|Deployment)(?:\s+\w+){0,3}[\s\S]{0,1000}",
                r"(?:Production|Scaling|Infrastructure)[\s\S]{0,1000}",
                r"(?:Kubernetes|Docker|Container)[\s\S]{0,1000}"
            ],
            "performance": [
                r"(?:Performance|Optimization)(?:\s+\w+){0,3}[\s\S]{0,1000}",
                r"(?:Latency|Throughput|Speed)[\s\S]{0,1000}",
                r"(?:Cache|Caching|Buffer)[\s\S]{0,1000}"
            ],
            "multimodal": [
                r"(?:Multi-?modal|Multimodal)(?:\s+\w+){0,3}[\s\S]{0,1000}",
                r"(?:Vision|Visual|Audio)\s+(?:Processing|Analysis)[\s\S]{0,1000}",
                r"(?:Speech|Text|Image)\s+(?:Recognition|Understanding)[\s\S]{0,1000}"
            ]
        }
        
        patterns = section_patterns.get(section_type, [])
        extracted_text = ""
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                extracted = match.group(0).strip()
                if len(extracted) > 100:  # Only keep substantial extracts
                    extracted_text += f"\n\n{extracted}"
        
        # Also extract bullet points and numbered lists related to the section
        if section_type in content.lower():
            list_patterns = [
                rf"{section_type}.*?:\s*\n((?:[-•*]\s*.+\n?)+)",
                rf"{section_type}.*?:\s*\n((?:\d+\.\s*.+\n?)+)"
            ]
            
            for pattern in list_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    extracted_text += f"\n\n{match.group(1).strip()}"
        
        return extracted_text.strip() if extracted_text else None
    
    def _extract_topic_context(self, content: str, topic: str, page_num: int) -> Optional[str]:
        """Extract context around a specific topic"""
        topic_lower = topic.lower()
        content_lower = content.lower()
        
        # Find all occurrences of the topic
        positions = []
        start = 0
        while True:
            pos = content_lower.find(topic_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        if not positions:
            return None
        
        # Extract context around each occurrence
        contexts = []
        context_size = 500  # Characters before and after
        
        for pos in positions:
            start = max(0, pos - context_size)
            end = min(len(content), pos + len(topic) + context_size)
            
            # Try to align with sentence boundaries
            context = content[start:end]
            
            # Find sentence start
            sentence_start = context.rfind('. ', 0, context_size)
            if sentence_start > 0:
                context = context[sentence_start + 2:]
            
            # Find sentence end
            sentence_end = context.find('. ', context_size + len(topic))
            if sentence_end > 0:
                context = context[:sentence_end + 1]
            
            contexts.append(context.strip())
        
        # Combine and deduplicate contexts
        unique_contexts = []
        for ctx in contexts:
            if not any(ctx in existing for existing in unique_contexts):
                unique_contexts.append(ctx)
        
        return "\n\n---\n\n".join(unique_contexts)
    
    def _store_patterns_in_chroma(self, patterns: Dict[str, List[Dict]], source_pdf: str) -> None:
        """Store extracted patterns in ChromaDB"""
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                try:
                    # Create unique ID
                    pattern_id = self._generate_id(
                        f"{source_pdf}_{pattern_type}",
                        pattern['content'][:100]
                    )
                    
                    # Create embedding
                    embedding = self.embeddings.embed_query(pattern['content'])
                    
                    # Store in ChromaDB
                    self.pdf_collection.add(
                        embeddings=[embedding],
                        documents=[pattern['content']],
                        metadatas=[{
                            "source": source_pdf,
                            "page": pattern.get('page', 0),
                            "pattern_type": pattern_type,
                            "type": pattern.get('type', pattern_type),
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[pattern_id]
                    )
                except Exception as e:
                    print(f"Error storing pattern in ChromaDB: {e}")
                    continue
    
    def _store_topic_extracts_in_chroma(self, topic_results: Dict[str, List[Dict]], source_pdf: str) -> None:
        """Store topic extracts in ChromaDB"""
        for topic, extracts in topic_results.items():
            for extract in extracts:
                try:
                    # Create unique ID
                    extract_id = self._generate_id(
                        f"{source_pdf}_{topic}",
                        extract['content'][:100]
                    )
                    
                    # Create embedding
                    embedding = self.embeddings.embed_query(extract['content'])
                    
                    # Store in ChromaDB
                    self.pdf_collection.add(
                        embeddings=[embedding],
                        documents=[extract['content']],
                        metadatas=[{
                            "source": source_pdf,
                            "page": extract.get('page', 0),
                            "topic": topic,
                            "type": "topic_extract",
                            "extracted_at": datetime.now().isoformat()
                        }],
                        ids=[extract_id]
                    )
                except Exception as e:
                    print(f"Error storing topic extract in ChromaDB: {e}")
                    continue
    
    def analyze_pdf_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze PDF structure to understand content organization"""
        structure = {
            "total_pages": 0,
            "sections": [],
            "figures": 0,
            "tables": 0,
            "code_blocks": 0,
            "key_topics": []
        }
        
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            structure["total_pages"] = len(pages)
            
            # Analyze each page
            all_content = ""
            for page_num, page in enumerate(pages):
                content = page.page_content
                all_content += content + "\n"
                
                # Detect sections (headers)
                section_patterns = [
                    r"^#+\s+(.+)$",  # Markdown headers
                    r"^(\d+\.?\d*)\s+([A-Z].+)$",  # Numbered sections
                    r"^([A-Z][A-Z\s]+)$"  # All caps headers
                ]
                
                for pattern in section_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        section_title = match.group(1) if match.lastindex == 1 else match.group(2)
                        structure["sections"].append({
                            "title": section_title.strip(),
                            "page": page_num + 1
                        })
                
                # Count figures and tables
                structure["figures"] += len(re.findall(r"(?:Figure|Fig\.?)\s+\d+", content, re.IGNORECASE))
                structure["tables"] += len(re.findall(r"(?:Table)\s+\d+", content, re.IGNORECASE))
                
                # Count code blocks
                structure["code_blocks"] += len(re.findall(r"```[\s\S]*?```", content))
            
            # Extract key topics using frequency analysis
            topic_candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", all_content)
            topic_freq = {}
            for topic in topic_candidates:
                if len(topic) > 5 and topic not in ["The", "This", "These", "That", "There"]:
                    topic_freq[topic] = topic_freq.get(topic, 0) + 1
            
            # Get top topics
            structure["key_topics"] = sorted(
                topic_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
        except Exception as e:
            print(f"Error analyzing PDF structure: {e}")
            
        return structure
    
    def extract_code_examples(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract code examples from PDF"""
        code_examples = []
        
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            for page_num, page in enumerate(pages):
                content = page.page_content
                
                # Pattern for code blocks
                code_patterns = [
                    r"```(\w*)\n([\s\S]*?)```",  # Markdown code blocks
                    r"(?:Code|Example|Listing)\s*\d*:?\s*\n([\s\S]{50,500})",  # Labeled code
                    r"(?:^\s{4,}|\t+)(.+)$"  # Indented code
                ]
                
                for pattern in code_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        if match.lastindex == 2:  # Markdown with language
                            language = match.group(1) or "unknown"
                            code = match.group(2).strip()
                        else:
                            language = "unknown"
                            code = match.group(1).strip() if match.lastindex == 1 else match.group(0).strip()
                        
                        # Only keep substantial code blocks
                        if len(code) > 50 and not all(line.startswith("#") for line in code.split("\n")):
                            code_examples.append({
                                "code": code,
                                "language": language,
                                "page": page_num + 1,
                                "source": Path(pdf_path).name
                            })
                
        except Exception as e:
            print(f"Error extracting code examples: {e}")
            
        return code_examples
    
    def _generate_id(self, source: str, content: str) -> str:
        """Generate unique ID for content"""
        combined = f"{source}:{content}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]