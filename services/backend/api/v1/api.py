"""
Main API router that combines all v1 endpoints
"""
from fastapi import APIRouter
from .routers import video_analysis_router

# Create main v1 router
api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(video_analysis_router)

# Additional routers can be added here as the project grows:
# api_router.include_router(projects_router)
# api_router.include_router(knowledge_graph_router)
# api_router.include_router(search_router)