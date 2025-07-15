"""
RAG (Retrieval-Augmented Generation) tasks for runtime queries.

These are lightweight tasks for the runtime phase of the Video Intelligence Platform.
"""

from celery import Task
from celery_app import celery_app
from utils.memory_monitor import monitor_memory
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='workers.rag_tasks.semantic_search')
@monitor_memory(threshold_mb=1000)  # Lightweight - 1GB limit
def semantic_search(self, query: str, project_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform semantic search across video content.
    
    Args:
        query: Search query
        project_id: Project ID to search within
        filters: Optional filters (time range, video IDs, etc.)
        
    Returns:
        Search results with relevance scores
    """
    from services.rag.semantic_searcher import SemanticSearcher
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'searching',
            'query': query[:100]  # Truncate for display
        })
        
        searcher = SemanticSearcher()
        
        # Generate query embedding
        query_embedding = searcher.embed_query(query)
        
        # Search in vector database
        results = searcher.search(
            query_embedding=query_embedding,
            project_id=project_id,
            filters=filters,
            top_k=20  # Get top 20 results
        )
        
        # Re-rank results
        reranked = searcher.rerank_results(
            query=query,
            results=results,
            top_k=10  # Return top 10 after reranking
        )
        
        return {
            'query': query,
            'project_id': project_id,
            'total_results': len(reranked),
            'results': reranked
        }
        
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=30)


@celery_app.task(bind=True, name='workers.rag_tasks.graph_traversal_search')
@monitor_memory(threshold_mb=1500)  # Graph operations need more memory
def graph_traversal_search(self, entity_id: str, relationship_types: List[str], max_depth: int = 2) -> Dict[str, Any]:
    """
    Search knowledge graph by traversing relationships from an entity.
    
    Args:
        entity_id: Starting entity ID
        relationship_types: Types of relationships to follow
        max_depth: Maximum traversal depth
        
    Returns:
        Connected entities and relationships
    """
    from services.rag.graph_searcher import GraphSearcher
    
    try:
        searcher = GraphSearcher()
        
        # Perform graph traversal
        subgraph = searcher.traverse_from_entity(
            entity_id=entity_id,
            relationship_types=relationship_types,
            max_depth=max_depth
        )
        
        # Extract relevant information
        connected_entities = searcher.extract_entities(subgraph)
        paths = searcher.extract_paths(subgraph)
        
        return {
            'entity_id': entity_id,
            'traversal_depth': max_depth,
            'connected_entities': connected_entities,
            'relationship_paths': paths,
            'subgraph_size': len(subgraph['nodes'])
        }
        
    except Exception as e:
        logger.error(f"Graph traversal failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.rag_tasks.hybrid_search')
def hybrid_search(self, query: str, project_id: str, search_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform hybrid search combining vector similarity and graph traversal.
    
    Args:
        query: Search query
        project_id: Project ID
        search_config: Configuration for search weights and parameters
        
    Returns:
        Combined search results
    """
    from services.rag.hybrid_searcher import HybridSearcher
    
    try:
        searcher = HybridSearcher()
        
        # Configure search weights
        vector_weight = search_config.get('vector_weight', 0.7)
        graph_weight = search_config.get('graph_weight', 0.3)
        
        # Perform hybrid search
        results = searcher.search(
            query=query,
            project_id=project_id,
            vector_weight=vector_weight,
            graph_weight=graph_weight,
            filters=search_config.get('filters', {})
        )
        
        return {
            'query': query,
            'project_id': project_id,
            'search_type': 'hybrid',
            'total_results': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.rag_tasks.generate_context')
@monitor_memory(threshold_mb=2000)
def generate_context(self, query: str, search_results: List[Dict[str, Any]], max_context_length: int = 4000) -> Dict[str, Any]:
    """
    Generate context from search results for LLM response.
    
    Args:
        query: Original query
        search_results: Results from search
        max_context_length: Maximum context length in tokens
        
    Returns:
        Generated context for LLM
    """
    from services.rag.context_generator import ContextGenerator
    
    try:
        generator = ContextGenerator()
        
        # Extract and format relevant content
        context_parts = []
        
        for result in search_results:
            # Extract different types of content
            if result['type'] == 'transcript':
                context_parts.append(generator.format_transcript(result))
            elif result['type'] == 'scene':
                context_parts.append(generator.format_scene(result))
            elif result['type'] == 'entity':
                context_parts.append(generator.format_entity(result))
            elif result['type'] == 'relationship':
                context_parts.append(generator.format_relationship(result))
        
        # Combine and trim to fit context window
        context = generator.combine_context(
            parts=context_parts,
            query=query,
            max_length=max_context_length
        )
        
        return {
            'query': query,
            'context': context,
            'sources': [r['source'] for r in search_results],
            'context_length': len(context)
        }
        
    except Exception as e:
        logger.error(f"Context generation failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.rag_tasks.answer_query')
def answer_query(self, query: str, context: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Generate answer using LLM with retrieved context.
    
    Args:
        query: User query
        context: Retrieved context
        conversation_history: Previous conversation turns
        
    Returns:
        Generated answer with metadata
    """
    from services.rag.answer_generator import AnswerGenerator
    
    try:
        generator = AnswerGenerator()
        
        # Generate answer
        answer = generator.generate_answer(
            query=query,
            context=context,
            conversation_history=conversation_history or [],
            model='gpt-4'  # Can be configured
        )
        
        # Extract citations from answer
        citations = generator.extract_citations(answer['response'])
        
        return {
            'query': query,
            'answer': answer['response'],
            'citations': citations,
            'model': answer['model'],
            'tokens_used': answer['tokens'],
            'confidence': answer.get('confidence', 1.0)
        }
        
    except Exception as e:
        logger.error(f"Answer generation failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.rag_tasks.extract_video_moments')
def extract_video_moments(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract specific video moments/timestamps relevant to query.
    
    Args:
        query: User query
        search_results: Search results with timestamps
        
    Returns:
        Relevant video moments
    """
    from services.rag.moment_extractor import MomentExtractor
    
    try:
        extractor = MomentExtractor()
        
        # Extract moments from search results
        moments = extractor.extract_moments(
            query=query,
            results=search_results
        )
        
        # Group by video
        moments_by_video = extractor.group_by_video(moments)
        
        # Create highlight reel
        highlights = extractor.create_highlights(
            moments_by_video,
            max_duration=300  # 5 minutes max
        )
        
        return {
            'query': query,
            'total_moments': len(moments),
            'videos_found': len(moments_by_video),
            'moments': moments,
            'highlights': highlights
        }
        
    except Exception as e:
        logger.error(f"Moment extraction failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.rag_tasks.update_conversation_context')
def update_conversation_context(self, conversation_id: str, turn: Dict[str, str]) -> Dict[str, Any]:
    """
    Update conversation context for multi-turn interactions.
    
    Args:
        conversation_id: Conversation ID
        turn: New conversation turn (query/response)
        
    Returns:
        Updated conversation state
    """
    from services.rag.conversation_manager import ConversationManager
    
    try:
        manager = ConversationManager()
        
        # Update conversation
        updated = manager.add_turn(conversation_id, turn)
        
        # Summarize if needed
        if updated['turn_count'] > 10:
            summary = manager.summarize_conversation(conversation_id)
            updated['summary'] = summary
        
        return updated
        
    except Exception as e:
        logger.error(f"Conversation update failed: {str(e)}", exc_info=True)
        raise