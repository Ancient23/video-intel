#!/usr/bin/env python3
"""
Initialize MongoDB with base ProjectStatus data
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from dotenv import load_dotenv

# Add project to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "services" / "backend"))

from models import ProjectStatus, TechnicalDebt
from models.project_status import ProjectPhase, ComponentStatus as ComponentStatusEnum

load_dotenv()

async def initialize_project_status():
    # Connect to MongoDB
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/video-intelligence")
    client = AsyncIOMotorClient(mongo_url)
    db_name = mongo_url.split("/")[-1].split("?")[0]
    db = client[db_name]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[ProjectStatus, TechnicalDebt])
    
    # Check if project status already exists
    existing = await ProjectStatus.find_one({"project_name": "video-intelligence-platform"})
    if existing:
        print("✅ ProjectStatus already exists")
        return
    
    # Create initial project status
    project_status = ProjectStatus(
        project_name="video-intelligence-platform",
        current_phase=ProjectPhase.KNOWLEDGE_BUILDING,
        components={
            "mongodb_setup": ComponentStatusEnum.COMPLETED,
            "video_chunking": ComponentStatusEnum.NOT_STARTED,
            "provider_architecture": ComponentStatusEnum.NOT_STARTED,
            "knowledge_graph": ComponentStatusEnum.COMPLETED,
            "embeddings": ComponentStatusEnum.COMPLETED,
            "rag_system": ComponentStatusEnum.COMPLETED,
            "api_endpoints": ComponentStatusEnum.IN_PROGRESS,
            "websocket_support": ComponentStatusEnum.NOT_STARTED,
            "conversation_engine": ComponentStatusEnum.NOT_STARTED,
            "testing_suite": ComponentStatusEnum.NOT_STARTED
        },
        completed_tasks=[
            "Migrated from ChromaDB to Qdrant+Neo4j for Graph-RAG",
            "Populated knowledge base with 1167 documents from NVIDIA Blueprints", 
            "Set up Docker infrastructure with all core services",
            "Created development CLI tools and prompt system",
            "Fixed health checks for Neo4j and Qdrant services",
            "Implemented Graph-RAG knowledge base with entity extraction",
            "Created comprehensive prompt templates for all workflows"
        ],
        current_tasks=[
            "Implement authentication system",
            "Create video chunking service with FFmpeg",
            "Integrate AWS Rekognition provider"
        ],
        blocked_tasks=[],
        test_coverage=0.0,
        api_endpoints_completed=3,
        providers_integrated=[],
        notes=[
            {"date": datetime.utcnow().isoformat(), "note": "Graph-RAG system fully operational"},
            {"date": datetime.utcnow().isoformat(), "note": "Knowledge base contains NVIDIA Blueprints and infrastructure docs"}
        ],
        known_issues=[
            {"issue": "Flower monitoring UI fails to start", "severity": "low"},
            {"issue": "No authentication system", "severity": "critical"}
        ]
    )
    
    await project_status.save()
    print("✅ ProjectStatus initialized successfully")
    
    # Create some initial technical debt entries
    tech_debts = [
        TechnicalDebt(
            title="Authentication System Missing",
            description="No authentication system implemented yet - critical for production",
            category="security",
            severity="high",
            effort_estimate="2-3 days",
            components_affected=["api_service", "frontend"],
            created_by="system"
        ),
        TechnicalDebt(
            title="No Test Coverage",
            description="Project has no unit or integration tests",
            category="testing",
            severity="medium",
            effort_estimate="1 week",
            components_affected=["all"],
            created_by="system"
        ),
        TechnicalDebt(
            title="Flower Monitoring UI Import Errors",
            description="Celery Flower monitoring UI fails to start due to import errors",
            category="infrastructure",
            severity="low",
            effort_estimate="2-4 hours",
            components_affected=["worker", "monitoring"],
            created_by="system"
        )
    ]
    
    for debt in tech_debts:
        await debt.save()
    
    print(f"✅ Created {len(tech_debts)} technical debt entries")
    print("\n📊 Project Status Summary:")
    print(f"  - Current Phase: {project_status.current_phase.value}")
    print(f"  - Completed Tasks: {len(project_status.completed_tasks)}")
    print(f"  - Current Tasks: {len(project_status.current_tasks)}")
    print(f"  - Components: {len(project_status.components)}")
    print(f"  - Technical Debts: {len(tech_debts)}")

if __name__ == "__main__":
    asyncio.run(initialize_project_status())