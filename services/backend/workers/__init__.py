"""
Workers package for Video Intelligence Platform Celery tasks.

This package contains all Celery task modules organized by the two-phase architecture:

Phase 1 - Ingestion (Heavy Processing):
- ingestion_tasks: Main ingestion orchestration
- video_analysis_tasks: Video analysis with multiple providers
- embedding_tasks: Embedding generation for vectors
- knowledge_graph_tasks: Knowledge graph construction

Phase 2 - Runtime (Lightweight):
- rag_tasks: RAG queries and retrieval

Supporting:
- orchestration_tasks: Task coordination and workflow management
"""