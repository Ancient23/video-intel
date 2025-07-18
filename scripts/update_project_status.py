#!/usr/bin/env python3
"""
Update MongoDB project status after completing ingestion phase work
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
from models.technical_debt import TechnicalDebtItem, DebtSeverity, DebtCategory, DebtStatus

load_dotenv()

async def update_project_status():
    # Connect to MongoDB
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/video-intelligence")
    client = AsyncIOMotorClient(mongo_url)
    db_name = mongo_url.split("/")[-1].split("?")[0]
    db = client[db_name]
    
    # Initialize Beanie
    await init_beanie(database=db, document_models=[ProjectStatus, TechnicalDebt])
    
    # Get existing project status
    status = await ProjectStatus.find_one({"project_name": "video-intelligence-platform"})
    if not status:
        print("❌ ProjectStatus not found")
        return
    
    # Update component statuses
    status.update_component("video_chunking", ComponentStatusEnum.COMPLETED)
    status.update_component("api_endpoints", ComponentStatusEnum.IN_PROGRESS)  # Celery integration done
    
    # Add completed tasks
    new_completed_tasks = [
        "Implemented fixed-duration video chunking with model-specific defaults",
        "Completed API-Celery integration for async video processing",
        "Created comprehensive VideoMemory data structure for ingestion results",
        "Updated PRD to include transcription in ingestion phase",
        "Added support for AWS Transcribe and NVIDIA Riva in schemas",
        "Integrated memory system building into orchestration service"
    ]
    
    for task in new_completed_tasks:
        status.add_completed_task(task)
    
    # Update current tasks
    status.current_tasks = [
        "Integrate AWS Rekognition for timestamp extraction",
        "Implement NVIDIA VILA for prompt-based frame analysis", 
        "Add AWS Transcribe for audio transcription",
        "Set up S3 bucket structure for organized storage",
        "Create comprehensive tests for ingestion pipeline"
    ]
    
    # Add implementation note
    status.add_note(
        "Completed core ingestion infrastructure: fixed chunking, memory system, and API-Celery integration. Ready for provider implementations.",
        "implementation"
    )
    
    # Update metrics
    status.api_endpoints_completed = 5  # Basic CRUD + analysis endpoints
    
    # Save updates
    await status.save()
    
    print("✅ ProjectStatus updated successfully")
    
    # Create technical debt document if doesn't exist
    tech_debt_doc = await TechnicalDebt.find_one()
    if not tech_debt_doc:
        tech_debt_doc = TechnicalDebt(items=[])
        await tech_debt_doc.save()
    
    # Add new technical debt items
    # Define new technical debt items
    new_debt_items = [
        TechnicalDebtItem(
            id="ORCH-001",
            title="Missing Error Handling in Orchestration Service",
            description="The orchestration service needs better error handling for provider failures and partial results",
            category=DebtCategory.ERROR_HANDLING,
            severity=DebtSeverity.MEDIUM,
            estimated_effort_hours=8,
            tags=["orchestration_service", "provider_orchestrator"],
            status=DebtStatus.OPEN
        ),
        TechnicalDebtItem(
            id="ORCH-002",
            title="No Retry Logic for Failed Chunks",
            description="Individual chunk processing failures should be retryable without reprocessing entire video",
            category=DebtCategory.ERROR_HANDLING,
            severity=DebtSeverity.MEDIUM,
            estimated_effort_hours=12,
            tags=["video_chunker", "orchestration_service"],
            status=DebtStatus.OPEN
        ),
        TechnicalDebtItem(
            id="ORCH-003",
            title="Hardcoded Provider in Memory Building",
            description="TemporalMarker provider is hardcoded to AWS_REKOGNITION, should be extracted from actual results",
            category=DebtCategory.HARDCODED,
            severity=DebtSeverity.LOW,
            estimated_effort_hours=2,
            tags=["orchestration_service"],
            status=DebtStatus.OPEN
        ),
        TechnicalDebtItem(
            id="EMB-001",
            title="Missing Embedding Generation",
            description="VideoMemory chunks don't have embeddings generated yet - needed for semantic search",
            category=DebtCategory.INCOMPLETE,
            severity=DebtSeverity.HIGH,
            estimated_effort_hours=20,
            tags=["orchestration_service", "embeddings"],
            status=DebtStatus.OPEN
        ),
        TechnicalDebtItem(
            id="INFRA-001",
            title="No S3 Lifecycle Policies",
            description="Need to implement S3 lifecycle policies for automatic cleanup of old chunks",
            category=DebtCategory.CONFIGURATION,
            severity=DebtSeverity.LOW,
            estimated_effort_hours=4,
            tags=["s3_utils"],
            status=DebtStatus.OPEN
        ),
        TechnicalDebtItem(
            id="TEST-001",
            title="Missing Integration Tests",
            description="No integration tests for full ingestion pipeline - only unit tests exist",
            category=DebtCategory.TESTING,
            severity=DebtSeverity.HIGH,
            estimated_effort_hours=28,
            tags=["all_ingestion_components", "integration_tests"],
            status=DebtStatus.OPEN
        )
    ]
    
    # Add technical debt items if they don't exist
    added_count = 0
    for item in new_debt_items:
        # Determine component based on first tag
        component = item.tags[0] if item.tags else "general"
        
        # Check if already exists by ID
        existing_ids = set()
        if component in tech_debt_doc.debt_items:
            existing_ids = {debt.id for debt in tech_debt_doc.debt_items[component]}
        
        if item.id not in existing_ids:
            tech_debt_doc.add_debt_item(component, item)
            added_count += 1
            print(f"✅ Added technical debt: {item.title}")
        else:
            print(f"⏭️  Technical debt already exists: {item.title}")
    
    # Save if we added new items
    if added_count > 0:
        await tech_debt_doc.save()
    
    # Print summary
    print("\n📊 Updated Project Status:")
    print(f"  - Current Phase: {status.current_phase.value}")
    print(f"  - Video Chunking: {status.components['video_chunking'].value}")
    print(f"  - API Endpoints: {status.components['api_endpoints'].value}")
    print(f"  - Total Completed Tasks: {len(status.completed_tasks)}")
    print(f"  - Current Tasks: {len(status.current_tasks)}")
    print(f"  - New Technical Debts Added: {added_count}")
    print(f"  - Total Technical Debts: {tech_debt_doc.total_items}")
    
    # Show next priorities
    print("\n🎯 Next Priorities:")
    for i, task in enumerate(status.current_tasks[:3], 1):
        print(f"  {i}. {task}")

if __name__ == "__main__":
    asyncio.run(update_project_status())