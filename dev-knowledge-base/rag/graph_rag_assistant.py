"""
Graph-RAG Development Assistant

This module implements Graph-RAG capabilities by combining:
- Qdrant for vector similarity search
- Neo4j for graph-based relationship traversal
- LangChain for orchestration
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import json

# Lazy imports to avoid initialization issues
py2neo = None
Graph = None
qdrant_client = None
QdrantClient = None
models = None
openai = None
langchain_openai = None
langchain_qdrant = None

logger = logging.getLogger(__name__)


class GraphRAGAssistant:
    """Graph-RAG assistant combining vector and graph search"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.qdrant_client = None
        self.neo4j_graph = None
        self.embeddings = None
        self.llm = None
        self.collection_name = None
        self._initialized = False
    
    def _lazy_init(self):
        """Initialize components only when needed"""
        if self._initialized:
            return
        
        # Import modules
        global py2neo, Graph, qdrant_client, QdrantClient, models
        global openai, langchain_openai, langchain_qdrant
        
        try:
            # Graph database imports
            import py2neo as py2neo_module
            from py2neo import Graph as GraphClass
            py2neo = py2neo_module
            Graph = GraphClass
            
            # Vector database imports
            from qdrant_client import QdrantClient as QClient
            from qdrant_client import models as qdrant_models
            QdrantClient = QClient
            models = qdrant_models
            
            # AI imports
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
            
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            raise
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize Qdrant
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "video_intelligence_kb")
        
        try:
            self.qdrant_client = QdrantClient(url=qdrant_url)
            logger.info(f"Connected to Qdrant at {qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
        
        # Initialize Neo4j
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
        
        try:
            self.neo4j_graph = Graph(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info(f"Connected to Neo4j at {neo4j_uri}")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Graph features will be limited.")
            self.neo4j_graph = None
        
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
        logger.info("Graph-RAG Assistant initialized")
    
    def search(self, query: str, limit: int = 10, use_graph: bool = True) -> List[Dict[str, Any]]:
        """
        Search using both vector similarity and graph relationships
        
        Args:
            query: Search query
            limit: Maximum results to return
            use_graph: Whether to enhance results with graph traversal
            
        Returns:
            Combined and ranked results
        """
        self._lazy_init()
        
        results = []
        
        # 1. Vector search in Qdrant
        vector_results = self._vector_search(query, limit * 2)  # Get more for filtering
        results.extend(vector_results)
        
        # 2. Graph-enhanced search if available
        if use_graph and self.neo4j_graph:
            graph_results = self._graph_enhanced_search(query, vector_results, limit)
            results.extend(graph_results)
        
        # 3. Deduplicate and rank results
        final_results = self._rank_and_deduplicate(results, limit)
        
        return final_results
    
    def _vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform vector similarity search in Qdrant"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    'id': result.id,
                    'score': result.score,
                    'source': 'vector',
                    'text': result.payload.get('text', ''),
                    'metadata': {k: v for k, v in result.payload.items() if k != 'text'}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _graph_enhanced_search(self, query: str, vector_results: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """Enhance search results using graph relationships"""
        if not self.neo4j_graph or not vector_results:
            return []
        
        try:
            # Extract entities from query
            query_entities = self._extract_query_entities(query)
            
            # Get node IDs from vector results
            node_ids = [r['id'] for r in vector_results[:5]]  # Top 5 vector results
            
            # Query Neo4j for related nodes
            cypher_query = """
            // Find nodes matching our vector results
            MATCH (n:KnowledgeNode)
            WHERE n.id IN $node_ids
            
            // Find related nodes through various relationships
            OPTIONAL MATCH (n)-[r1:SIMILAR_TO|MENTIONS|RELATED_TO]-(related1:KnowledgeNode)
            OPTIONAL MATCH (n)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(related2:KnowledgeNode)
            WHERE e.name IN $entities
            
            // Collect unique related nodes
            WITH n, collect(DISTINCT related1) + collect(DISTINCT related2) as related_nodes
            UNWIND related_nodes as related
            
            // Return related nodes with relationship info
            RETURN DISTINCT related.id as id, 
                   related.title as title,
                   related.category as category,
                   related.source_file as source_file,
                   count(*) as connection_count
            ORDER BY connection_count DESC
            LIMIT $limit
            """
            
            results = self.neo4j_graph.run(
                cypher_query,
                node_ids=node_ids,
                entities=query_entities,
                limit=limit
            )
            
            graph_results = []
            for record in results:
                # Fetch full content from Qdrant if available
                content = self._fetch_content_from_qdrant(record['id'])
                
                graph_results.append({
                    'id': record['id'],
                    'score': 0.7 + (0.1 * min(record['connection_count'], 3)),  # Graph relevance score
                    'source': 'graph',
                    'text': content or f"{record['title']}\n\nCategory: {record['category']}",
                    'metadata': {
                        'title': record['title'],
                        'category': record['category'],
                        'source_file': record['source_file'],
                        'connection_count': record['connection_count']
                    }
                })
            
            return graph_results
            
        except Exception as e:
            logger.warning(f"Graph search failed: {e}")
            return []
    
    def _extract_query_entities(self, query: str) -> List[str]:
        """Extract entities from query (simple keyword matching)"""
        # Common technical entities
        entities = []
        keywords = [
            "qdrant", "neo4j", "mongodb", "redis", "docker", "aws", "s3",
            "rag", "graph-rag", "embedding", "vector", "langchain", "openai",
            "video", "chunk", "analysis", "knowledge", "graph"
        ]
        
        query_lower = query.lower()
        for keyword in keywords:
            if keyword in query_lower:
                entities.append(keyword.title() if len(keyword) > 3 else keyword.upper())
        
        return entities
    
    def _fetch_content_from_qdrant(self, node_id: str) -> Optional[str]:
        """Fetch full content from Qdrant by ID"""
        try:
            result = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[node_id],
                with_payload=True
            )
            if result:
                return result[0].payload.get('text', '')
        except:
            pass
        return None
    
    def _rank_and_deduplicate(self, results: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """Rank and deduplicate combined results"""
        # Deduplicate by ID
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        # Sort by score (higher is better)
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Add ranking information
        for i, result in enumerate(unique_results[:limit]):
            result['rank'] = i + 1
        
        return unique_results[:limit]
    
    def ask(self, question: str, context_limit: int = 5, use_graph: bool = True) -> str:
        """
        Ask a question using Graph-RAG
        
        Args:
            question: The question to answer
            context_limit: Number of context documents to use
            use_graph: Whether to use graph enhancement
            
        Returns:
            Answer generated using retrieved context
        """
        self._lazy_init()
        
        # Search for relevant context
        results = self.search(question, limit=context_limit * 2, use_graph=use_graph)
        
        if not results:
            return "I couldn't find any relevant information in the knowledge base."
        
        # Build context from search results
        context_parts = []
        sources_used = {'vector': 0, 'graph': 0}
        
        for i, result in enumerate(results[:context_limit]):
            source = result['source']
            sources_used[source] += 1
            
            source_file = result['metadata'].get('source_file', 'Unknown')
            text = result['text']
            
            context_parts.append(f"[{source.upper()} Source {i+1}: {source_file}]\n{text}")
        
        context = "\n\n".join(context_parts)
        
        # Generate response with source attribution
        prompt = f"""Based on the following context from the Video Intelligence Platform knowledge base, 
please answer the question. The context includes both direct matches (VECTOR) and related information (GRAPH).

Context:
{context}

Question: {question}

Answer (mention which type of sources were most helpful):"""
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content
            
            # Add source summary
            source_summary = f"\n\n📊 Sources used: {sources_used['vector']} vector matches, {sources_used['graph']} graph relationships"
            
            return answer + source_summary
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {str(e)}"
    
    def explore_relationships(self, entity: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Explore graph relationships for a given entity
        
        Args:
            entity: Entity name to explore
            max_depth: Maximum relationship depth
            
        Returns:
            Graph structure around the entity
        """
        self._lazy_init()
        
        if not self.neo4j_graph:
            return {"error": "Neo4j not available"}
        
        try:
            # Query for entity relationships
            cypher_query = """
            MATCH path = (e:Entity {name: $entity})-[*1..$depth]-(connected)
            WITH e, connected, path
            RETURN e.name as entity,
                   type(connected) as connected_type,
                   connected.name as connected_name,
                   connected.title as connected_title,
                   length(path) as depth,
                   [rel in relationships(path) | type(rel)] as relationship_types
            ORDER BY depth, connected_type
            LIMIT 50
            """
            
            results = self.neo4j_graph.run(
                cypher_query,
                entity=entity,
                depth=max_depth
            )
            
            # Build relationship graph
            graph = {
                "entity": entity,
                "connections": []
            }
            
            for record in results:
                graph["connections"].append({
                    "type": record["connected_type"],
                    "name": record["connected_name"] or record["connected_title"],
                    "depth": record["depth"],
                    "relationships": record["relationship_types"]
                })
            
            return graph
            
        except Exception as e:
            logger.error(f"Failed to explore relationships: {e}")
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the Graph-RAG knowledge base"""
        self._lazy_init()
        
        stats = {
            "vector_db": {},
            "graph_db": {},
            "status": "healthy"
        }
        
        # Qdrant statistics
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            stats["vector_db"] = {
                "total_points": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": str(collection_info.config.params.vectors.distance)
            }
        except Exception as e:
            stats["vector_db"]["error"] = str(e)
            stats["status"] = "degraded"
        
        # Neo4j statistics
        if self.neo4j_graph:
            try:
                result = self.neo4j_graph.run("""
                    MATCH (n:KnowledgeNode) 
                    WITH count(n) as node_count
                    MATCH (e:Entity)
                    WITH node_count, count(e) as entity_count
                    MATCH ()-[r]->()
                    RETURN node_count, entity_count, count(r) as relationship_count
                """).data()
                
                if result:
                    stats["graph_db"] = result[0]
                else:
                    stats["graph_db"] = {
                        "node_count": 0,
                        "entity_count": 0,
                        "relationship_count": 0
                    }
            except Exception as e:
                stats["graph_db"]["error"] = str(e)
                stats["status"] = "degraded"
        else:
            stats["graph_db"]["status"] = "not connected"
        
        return stats