"""
Knowledge graph construction tasks for Video Intelligence Platform.

These tasks build and maintain the knowledge graph from video analysis results.
"""

from celery import Task
from celery_app import celery_app
from utils.memory_monitor import KnowledgeGraphTask, monitor_memory
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=KnowledgeGraphTask, name='workers.knowledge_graph_tasks.extract_entities')
def extract_entities(self, analysis_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Extract entities from video analysis results.
    
    Args:
        analysis_data: Analysis results from providers
        job_id: Processing job ID
        
    Returns:
        Extracted entities
    """
    from services.knowledge_graph.entity_extractor import EntityExtractor
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'extracting_entities',
            'job_id': job_id
        })
        
        extractor = EntityExtractor()
        entities = extractor.extract_from_analysis(analysis_data)
        
        # Group entities by type
        entity_groups = {
            'persons': [],
            'objects': [],
            'locations': [],
            'organizations': [],
            'events': [],
            'concepts': []
        }
        
        for entity in entities:
            entity_type = entity.get('type', 'objects')
            if entity_type in entity_groups:
                entity_groups[entity_type].append(entity)
        
        return {
            'job_id': job_id,
            'total_entities': len(entities),
            'entities_by_type': {k: len(v) for k, v in entity_groups.items()},
            'entities': entity_groups
        }
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, base=KnowledgeGraphTask, name='workers.knowledge_graph_tasks.extract_relationships')
def extract_relationships(self, entities: Dict[str, Any], analysis_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Extract relationships between entities.
    
    Args:
        entities: Extracted entities
        analysis_data: Original analysis data
        job_id: Processing job ID
        
    Returns:
        Extracted relationships
    """
    from services.knowledge_graph.relationship_extractor import RelationshipExtractor
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'extracting_relationships',
            'job_id': job_id
        })
        
        extractor = RelationshipExtractor()
        relationships = extractor.extract_relationships(
            entities=entities['entities'],
            context=analysis_data
        )
        
        # Group relationships by type
        relationship_types = {}
        for rel in relationships:
            rel_type = rel.get('type', 'related_to')
            if rel_type not in relationship_types:
                relationship_types[rel_type] = 0
            relationship_types[rel_type] += 1
        
        return {
            'job_id': job_id,
            'total_relationships': len(relationships),
            'relationships_by_type': relationship_types,
            'relationships': relationships
        }
        
    except Exception as e:
        logger.error(f"Relationship extraction failed: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=90)


@celery_app.task(bind=True, base=KnowledgeGraphTask, name='workers.knowledge_graph_tasks.build_scene_graph')
def build_scene_graph(self, chunk_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Build scene-level knowledge graph for a video chunk.
    
    Args:
        chunk_data: Analysis data for a chunk
        job_id: Processing job ID
        
    Returns:
        Scene graph data
    """
    from services.knowledge_graph.scene_graph_builder import SceneGraphBuilder
    
    try:
        builder = SceneGraphBuilder()
        
        # Extract scene information
        scene_data = {
            'chunk_id': chunk_data['chunk_id'],
            'timestamp': chunk_data.get('timestamp'),
            'duration': chunk_data.get('duration'),
            'objects': chunk_data.get('objects', []),
            'activities': chunk_data.get('activities', []),
            'settings': chunk_data.get('scenes', [])
        }
        
        # Build scene graph
        scene_graph = builder.build_graph(scene_data, job_id)
        
        return {
            'job_id': job_id,
            'chunk_id': chunk_data['chunk_id'],
            'scene_graph': scene_graph,
            'node_count': len(scene_graph['nodes']),
            'edge_count': len(scene_graph['edges'])
        }
        
    except Exception as e:
        logger.error(f"Scene graph construction failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, base=KnowledgeGraphTask, name='workers.knowledge_graph_tasks.merge_knowledge_graphs')
@monitor_memory(task_type='knowledge_graph')
def merge_knowledge_graphs(self, graph_components: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Merge multiple knowledge graph components into unified graph.
    
    Args:
        graph_components: List of graph components to merge
        job_id: Processing job ID
        
    Returns:
        Merged knowledge graph
    """
    from services.knowledge_graph.graph_merger import GraphMerger
    
    try:
        self.update_state(state='PROGRESS', meta={
            'stage': 'merging_graphs',
            'total_components': len(graph_components)
        })
        
        merger = GraphMerger()
        
        # Separate different types of components
        entity_data = []
        relationship_data = []
        scene_graphs = []
        
        for component in graph_components:
            if 'entities' in component:
                entity_data.append(component)
            elif 'relationships' in component:
                relationship_data.append(component)
            elif 'scene_graph' in component:
                scene_graphs.append(component)
        
        # Merge all components
        merged_graph = merger.merge(
            entities=entity_data,
            relationships=relationship_data,
            scene_graphs=scene_graphs,
            job_id=job_id
        )
        
        return {
            'job_id': job_id,
            'graph_id': merged_graph['graph_id'],
            'total_nodes': merged_graph['node_count'],
            'total_edges': merged_graph['edge_count'],
            'node_types': merged_graph['node_types'],
            'edge_types': merged_graph['edge_types']
        }
        
    except Exception as e:
        logger.error(f"Graph merging failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.knowledge_graph_tasks.persist_knowledge_graph')
def persist_knowledge_graph(self, graph_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Persist knowledge graph to database.
    
    Args:
        graph_data: Knowledge graph data
        job_id: Processing job ID
        
    Returns:
        Persistence results
    """
    from services.knowledge_graph.graph_storage import GraphStorage
    
    try:
        storage = GraphStorage()
        
        # Store graph in MongoDB
        result = storage.store_graph(
            graph_data=graph_data,
            job_id=job_id,
            metadata={
                'created_at': graph_data.get('created_at'),
                'video_id': graph_data.get('video_id'),
                'project_id': graph_data.get('project_id')
            }
        )
        
        # Create indexes for efficient querying
        storage.create_indexes(graph_id=result['graph_id'])
        
        return {
            'job_id': job_id,
            'graph_id': result['graph_id'],
            'storage_id': result['storage_id'],
            'indexed': True
        }
        
    except Exception as e:
        logger.error(f"Graph persistence failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.knowledge_graph_tasks.generate_graph_embeddings')
def generate_graph_embeddings(self, graph_id: str, job_id: str) -> Dict[str, Any]:
    """
    Generate embeddings for knowledge graph nodes and edges.
    
    Args:
        graph_id: Knowledge graph ID
        job_id: Processing job ID
        
    Returns:
        Graph embedding results
    """
    from services.knowledge_graph.graph_embedder import GraphEmbedder
    
    try:
        embedder = GraphEmbedder()
        
        # Generate node embeddings
        node_embeddings = embedder.embed_nodes(graph_id)
        
        # Generate edge embeddings (optional)
        edge_embeddings = embedder.embed_edges(graph_id)
        
        # Store embeddings
        embedder.store_embeddings(
            graph_id=graph_id,
            node_embeddings=node_embeddings,
            edge_embeddings=edge_embeddings
        )
        
        return {
            'job_id': job_id,
            'graph_id': graph_id,
            'node_embeddings_count': len(node_embeddings),
            'edge_embeddings_count': len(edge_embeddings),
            'embedding_dimension': embedder.dimension
        }
        
    except Exception as e:
        logger.error(f"Graph embedding generation failed: {str(e)}", exc_info=True)
        raise


@celery_app.task(bind=True, name='workers.knowledge_graph_tasks.update_graph_statistics')
def update_graph_statistics(self, graph_id: str, job_id: str) -> Dict[str, Any]:
    """
    Calculate and update knowledge graph statistics.
    
    Args:
        graph_id: Knowledge graph ID
        job_id: Processing job ID
        
    Returns:
        Graph statistics
    """
    from services.knowledge_graph.graph_analytics import GraphAnalytics
    
    try:
        analytics = GraphAnalytics()
        stats = analytics.calculate_statistics(graph_id)
        
        # Store statistics
        analytics.store_statistics(graph_id, stats)
        
        return {
            'job_id': job_id,
            'graph_id': graph_id,
            'statistics': stats
        }
        
    except Exception as e:
        logger.error(f"Graph statistics update failed: {str(e)}", exc_info=True)
        raise