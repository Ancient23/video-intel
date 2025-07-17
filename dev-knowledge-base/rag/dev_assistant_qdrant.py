"""
Development Assistant with Qdrant Vector Database

This module provides RAG capabilities using Qdrant for the development CLI.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

# Lazy imports to avoid initialization issues
qdrant_client = None
QdrantClient = None
models = None
Distance = None
VectorParams = None
openai = None
langchain_openai = None
langchain_qdrant = None
RecursiveCharacterTextSplitter = None

logger = logging.getLogger(__name__)

class DevelopmentAssistant:
    """RAG-based assistant using Qdrant for the dev CLI"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.client = None
        self.embeddings = None
        self.llm = None
        self.collection_name = None
        self._initialized = False
        
    def _lazy_init(self):
        """Initialize components only when needed"""
        if self._initialized:
            return
            
        # Import modules
        global qdrant_client, QdrantClient, models, Distance, VectorParams
        global openai, langchain_openai, langchain_qdrant, RecursiveCharacterTextSplitter
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
            models = type('models', (), {
                'Distance': Distance,
                'VectorParams': VectorParams,
                'PointStruct': PointStruct
            })()
            
            import openai as openai_module
            openai = openai_module
            
            from langchain_openai import OpenAIEmbeddings, ChatOpenAI
            langchain_openai = type('langchain_openai', (), {
                'OpenAIEmbeddings': OpenAIEmbeddings,
                'ChatOpenAI': ChatOpenAI
            })()
            
            from langchain_qdrant import QdrantVectorStore
            langchain_qdrant = type('langchain_qdrant', (), {
                'QdrantVectorStore': QdrantVectorStore
            })()
            
            from langchain.text_splitter import RecursiveCharacterTextSplitter as RCTSplitter
            RecursiveCharacterTextSplitter = RCTSplitter
            
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            raise
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize Qdrant client
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")
        
        try:
            self.client = QdrantClient(url=qdrant_url)
            logger.info(f"Connected to Qdrant at {qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
        
        # Initialize OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.embeddings = langchain_openai.OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        self.llm = langchain_openai.ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=api_key
        )
        
        self._initialized = True
        logger.info("Development Assistant initialized with Qdrant")
    
    def create_collection(self, recreate: bool = False):
        """Create or recreate the Qdrant collection"""
        self._lazy_init()
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(col.name == self.collection_name for col in collections)
            
            if exists and recreate:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            elif exists and not recreate:
                logger.info(f"Collection {self.collection_name} already exists")
                return
            
            # Create collection with 1536 dimensions (OpenAI embedding size)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Add documents to Qdrant collection"""
        self._lazy_init()
        self.create_collection()
        
        # Prepare documents for embedding
        texts = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            # Extract text content
            content = doc.get('content', '')
            title = doc.get('title', '')
            full_text = f"{title}\n\n{content}" if title else content
            
            texts.append(full_text)
            metadatas.append({
                'source_file': doc.get('source_file', ''),
                'category': doc.get('category', ''),
                'title': doc.get('title', ''),
                'importance': doc.get('importance', 3),
                'tags': doc.get('tags', []),
                'created_at': doc.get('created_at', datetime.utcnow().isoformat())
            })
            ids.append(f"{doc.get('category', 'unknown')}_{i}")
        
        # Split into batches and add to Qdrant
        total_added = 0
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            try:
                # Generate embeddings
                embeddings = self.embeddings.embed_documents(batch_texts)
                
                # Prepare points for Qdrant
                points = []
                for j, (embedding, metadata, doc_id) in enumerate(zip(embeddings, batch_metadatas, batch_ids)):
                    points.append(
                        models.PointStruct(
                            id=i + j,
                            vector=embedding,
                            payload={
                                **metadata,
                                'text': batch_texts[j]
                            }
                        )
                    )
                
                # Upload to Qdrant
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                total_added += len(points)
                logger.info(f"Added batch {i//batch_size + 1}, total: {total_added} documents")
                
            except Exception as e:
                logger.error(f"Failed to add batch: {e}")
                raise
        
        return total_added
    
    def search(self, query: str, limit: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search for similar documents in Qdrant"""
        self._lazy_init()
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                query_filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'score': result.score,
                    'text': result.payload.get('text', ''),
                    'metadata': {k: v for k, v in result.payload.items() if k != 'text'}
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def ask(self, question: str, context_limit: int = 5) -> str:
        """Ask a question using RAG"""
        self._lazy_init()
        
        # Search for relevant context
        results = self.search(question, limit=context_limit)
        
        if not results:
            return "I couldn't find any relevant information in the knowledge base."
        
        # Build context from search results
        context_parts = []
        for i, result in enumerate(results):
            source = result['metadata'].get('source_file', 'Unknown')
            text = result['text']
            context_parts.append(f"[Source {i+1}: {source}]\n{text}")
        
        context = "\n\n".join(context_parts)
        
        # Generate response
        prompt = f"""Based on the following context from the Video Intelligence Platform knowledge base, 
please answer the question. If the answer is not in the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {str(e)}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        self._lazy_init()
        
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                'total_documents': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': str(collection_info.config.params.vectors.distance),
                'status': 'healthy'
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                'total_documents': 0,
                'status': 'error',
                'error': str(e)
            }