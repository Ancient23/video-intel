"""
Main FastAPI application for Video Intelligence Platform
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from beanie import init_beanie
import motor.motor_asyncio

from .api.v1.api import api_router
from .core.database import get_database
from .models import (
    Video,
    ProcessingJob,
    Scene,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    ProjectStatus
)

# Document models for Beanie
document_models = [
    Video,
    ProcessingJob,
    Scene,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    ProjectStatus
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print("Starting Video Intelligence Platform API...")
    
    # Initialize database
    database = await get_database()
    await init_beanie(database=database, document_models=document_models)
    print("Database initialized")
    
    yield
    
    # Shutdown
    print("Shutting down Video Intelligence Platform API...")


# Create FastAPI app
app = FastAPI(
    title="Video Intelligence Platform",
    description="Advanced video analysis platform with RAG and knowledge graph capabilities",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "video-intelligence-api"}


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Video Intelligence Platform API",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "openapi": "/api/v1/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )