import os
from typing import Optional, Dict, List, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
import re
from dotenv import load_dotenv
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.lazy_init import with_timeout, LazyChromaDB, LazyOpenAI, debug_print


class DevelopmentAssistant:
    """RAG-powered development assistant"""
    
    def __init__(self, debug: bool = False):
        # Initialize OpenAI
        self.llm = None
        self.embeddings = None
        
        # ChromaDB client will be initialized on first use
        self.chroma_client = None
        self.collections = {}
        
        # Environment variables will be loaded lazily
        self._env_loaded = False
        self.chroma_type = None
        self.chroma_host = None
        self.chroma_port = None
        self.chroma_persist_path = None
        
        # Debug mode
        self.debug = debug
        
        # Lazy connections
        self._lazy_chromadb = None
        self._lazy_openai = None
    
    def _load_env(self):
        """Load environment variables lazily"""
        if not self._env_loaded:
            load_dotenv()
            self.chroma_type = os.getenv("CHROMA_CLIENT_TYPE", "persistent")
            self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
            self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
            self.chroma_persist_path = os.getenv("CHROMA_PERSIST_PATH", "./knowledge/chromadb")
            self._env_loaded = True
    
    def _init_openai(self):
        """Initialize OpenAI clients lazily"""
        if self.llm is None or self.embeddings is None:
            debug_print("Initializing OpenAI connection...", self.debug)
            try:
                # Don't use timeout decorator on the entire method
                # Just create the clients directly
                from langchain_openai import ChatOpenAI, OpenAIEmbeddings
                self.llm = ChatOpenAI(temperature=0, model_name="gpt-4")
                self.embeddings = OpenAIEmbeddings()
                debug_print("OpenAI connection established", self.debug)
            except Exception as e:
                debug_print(f"Error initializing OpenAI: {e}", self.debug)
                raise
    
    def _init_chromadb(self):
        """Initialize ChromaDB client lazily"""
        if self.chroma_client is not None:
            return
        
        # Load environment variables if not already loaded
        self._load_env()
        
        debug_print(f"Initializing ChromaDB ({self.chroma_type})...", self.debug)
        
        try:
            if self.chroma_type == "http":
                # Use HTTP client to connect to Docker ChromaDB
                self.chroma_client = chromadb.HttpClient(
                    host=self.chroma_host,
                    port=self.chroma_port,
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
            else:
                # Use persistent client for local development
                self.chroma_client = chromadb.PersistentClient(
                    path=self.chroma_persist_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            
            debug_print("ChromaDB connection established", self.debug)
        except Exception as e:
            debug_print(f"Error initializing ChromaDB: {e}", self.debug)
            raise
    
    def _get_collection(self, name: str) -> chromadb.Collection:
        """Get or cache a collection"""
        try:
            self._init_chromadb()  # Ensure ChromaDB is initialized
            
            if name not in self.collections:
                debug_print(f"Loading collection: {name}", self.debug)
                self.collections[name] = self.chroma_client.get_collection(name)
                
            return self.collections[name]
        except Exception as e:
            debug_print(f"Error getting collection {name}: {e}", self.debug)
            return None
    
    def query_patterns(self, query: str, category: Optional[str] = None) -> str:
        """Query implementation patterns"""
        
        # Determine which collections to search
        if category:
            collection_names = [category]
        else:
            # Search all relevant collections
            collection_names = [
                "lessons_learned",
                "architectural_decisions", 
                "implementation_guides",
                "api_documentation",
                "known_issues",
                "pdf_knowledge"
            ]
        
        try:
            # Generate query embedding using OpenAI
            self._init_openai()  # Ensure OpenAI is initialized
            
            try:
                query_embedding = self.embeddings.embed_query(query)
            except Exception as e:
                error_msg = f"Error generating query embedding: {e}"
                debug_print(error_msg, self.debug)
                return f"Error: Could not generate query embedding. Please check OpenAI API configuration.\n\nDetails: {str(e)}"
        except TimeoutError as e:
            return f"Error: OpenAI initialization timed out. Please check your API key and network connection.\n\nDetails: {str(e)}"
        except Exception as e:
            return f"Error: Failed to initialize OpenAI. {str(e)}"
        
        # Search in collections
        all_results = []
        collections_found = 0
        
        for collection_name in collection_names:
            try:
                collection = self._get_collection(collection_name)
                if not collection:
                    continue
                collections_found += 1
            except Exception as e:
                debug_print(f"Skipping collection {collection_name}: {e}", self.debug)
                continue
                
            try:
                # Query the collection with embeddings
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 1.0
                        
                        all_results.append({
                            "content": doc,
                            "metadata": metadata,
                            "collection": collection_name,
                            "relevance": 1.0 - distance  # Convert distance to relevance
                        })
            except Exception as e:
                print(f"Error querying collection {collection_name}: {e}")
                continue
        
        # Check if we found any collections
        if collections_found == 0:
            return f"Error: No ChromaDB collections found. The knowledge base appears to be empty.\n\nTo populate it, run:\npython scripts/populate_knowledge_base.py <old_repo_path> <pdf_dir>"
        
        # Sort by relevance
        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Take top results
        top_results = all_results[:10]
        
        # Format results for context
        context_parts = []
        for result in top_results:
            source = result["metadata"].get("source", "Unknown")
            collection = result["collection"]
            content = result["content"]
            
            context_parts.append(f"**Source**: {source} (from {collection})\n{content}\n")
        
        context = "\n---\n".join(context_parts)
        
        # If no results found
        if not context:
            return f"No relevant patterns found for: {query}\n\nThe knowledge base has {collections_found} collections but no matching content.\n\nTry a more general query or populate the knowledge base with more data."
        
        # Generate response with context
        prompt = f"""Based on the VideoCommentator project patterns and the new Video Intelligence architecture,
provide guidance for: {query}

Relevant patterns found:
{context}

Consider:
1. Lessons learned from the old implementation
2. New architectural requirements  
3. Best practices identified
4. Known issues and their solutions

Provide a concise, actionable response."""
        
        self._init_openai()  # Ensure OpenAI is initialized
        
        try:
            response = self.llm.invoke(prompt).content
            return response
        except Exception as e:
            return f"Error generating response: {e}\n\nContext found:\n{context}"
    
    def suggest_implementation(self, component: str) -> Dict[str, Any]:
        """Suggest implementation based on past patterns"""
        
        # Find similar components
        similar = self._find_similar_components(component)
        
        # Extract patterns
        patterns = self._extract_implementation_patterns(similar)
        
        return {
            "suggested_structure": patterns.get("structure", ["No specific structure found"]),
            "required_patterns": patterns.get("must_have", ["Follow general best practices"]),
            "common_pitfalls": patterns.get("pitfalls", ["No specific pitfalls identified"]),
            "reference_implementations": patterns.get("references", ["Check the old VideoCommentator codebase"])
        }
    
    def _find_similar_components(self, component: str) -> List[Dict]:
        """Find similar components in knowledge base"""
        similar = []
        
        # Generate query embedding
        self._init_openai()  # Ensure OpenAI is initialized
        
        try:
            query_text = f"{component} implementation pattern structure"
            query_embedding = self.embeddings.embed_query(query_text)
        except Exception as e:
            print(f"Error generating embedding for component search: {e}")
            return similar
        
        # Search for component patterns
        collections_to_search = ["implementation_guides", "architectural_decisions", "lessons_learned"]
        
        for collection_name in collections_to_search:
            collection = self._get_collection(collection_name)
            if not collection:
                continue
                
            try:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5,
                    include=["documents", "metadatas"]
                )
                
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        
                        similar.append({
                            "content": doc,
                            "metadata": metadata,
                            "collection": collection_name
                        })
            except Exception as e:
                print(f"Error searching for similar components: {e}")
                continue
        
        return similar
    
    def _extract_implementation_patterns(self, similar_components: List[Dict]) -> Dict[str, List[str]]:
        """Extract implementation patterns from similar components"""
        patterns = {
            "structure": [],
            "must_have": [],
            "pitfalls": [],
            "references": []
        }
        
        for component in similar_components:
            content = component["content"]
            metadata = component["metadata"]
            
            # Extract structure patterns
            structure_matches = re.findall(r"(?:structure|class|interface|module):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            patterns["structure"].extend(structure_matches)
            
            # Extract must-have patterns
            must_have_matches = re.findall(r"(?:must|always|require|should):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            patterns["must_have"].extend(must_have_matches)
            
            # Extract pitfalls
            pitfall_matches = re.findall(r"(?:pitfall|avoid|don't|never|issue):\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
            patterns["pitfalls"].extend(pitfall_matches)
            
            # Add reference
            source = metadata.get("source", "Unknown")
            patterns["references"].append(f"{source} ({component['collection']})")
        
        # Deduplicate
        for key in patterns:
            patterns[key] = list(set(patterns[key]))[:5]  # Keep top 5 unique items
        
        return patterns