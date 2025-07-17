#!/usr/bin/env python3
"""Initialize project status in MongoDB"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "services"))

from backend.core.database import init_database, Database
from backend.models import ProjectStatus, ProjectPhase, ComponentStatus


async def initialize_project_status():
    """Create or update project status document"""
    
    # Connect to database
    await init_database()
    
    try:
        # Check if project status already exists
        existing = await ProjectStatus.find_one({"project_name": "video-intelligence-platform"})
        
        if existing:
            print("Found existing project status, updating...")
            # Update existing status
            existing.updated_at = datetime.now(timezone.utc)
            existing.add_note("Dev environment initialized with MongoDB models", "setup")
            
            # Update component statuses based on what we've done
            existing.update_component("mongodb_setup", ComponentStatus.COMPLETED)
            
            await existing.save()
            status = existing
        else:
            print("Creating new project status...")
            # Create new project status
            status = ProjectStatus(
                current_phase=ProjectPhase.FOUNDATION,
                components={
                    "mongodb_setup": ComponentStatus.COMPLETED,
                    "video_chunking": ComponentStatus.NOT_STARTED,
                    "provider_architecture": ComponentStatus.NOT_STARTED,
                    "knowledge_graph": ComponentStatus.NOT_STARTED,
                    "embeddings": ComponentStatus.NOT_STARTED,
                    "rag_system": ComponentStatus.NOT_STARTED,
                    "api_endpoints": ComponentStatus.NOT_STARTED,
                    "websocket_support": ComponentStatus.NOT_STARTED,
                    "conversation_engine": ComponentStatus.NOT_STARTED,
                    "testing_suite": ComponentStatus.NOT_STARTED,
                },
                completed_tasks=[
                    "Set up project structure",
                    "Create development knowledge base",
                    "Design MongoDB schemas",
                    "Implement MongoDB models with Beanie",
                ],
                current_tasks=[
                    "Implement video chunking service",
                    "Create provider plugin architecture",
                    "Set up AWS Rekognition integration",
                ],
                notes=[{
                    "timestamp": datetime.now(timezone.utc),
                    "category": "setup",
                    "note": "Project initialized with MongoDB models and development knowledge base"
                }]
            )
            await status.create()
        
        # Print current status
        print("\n=== Project Status ===")
        print(f"Project: {status.project_name}")
        print(f"Phase: {status.current_phase}")
        print(f"Updated: {status.updated_at}")
        print("\nComponent Status:")
        for component, comp_status in status.components.items():
            emoji = "✅" if comp_status == ComponentStatus.COMPLETED else "⏳" if comp_status == ComponentStatus.IN_PROGRESS else "❌"
            print(f"  {emoji} {component}: {comp_status}")
        
        print(f"\nCompleted Tasks: {len(status.completed_tasks)}")
        print(f"Current Tasks: {len(status.current_tasks)}")
        
        if status.notes:
            print("\nLatest Note:")
            latest_note = status.notes[-1]
            print(f"  [{latest_note['category']}] {latest_note['note']}")
        
        print("\n✅ Project status initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing project status: {e}")
        raise
    finally:
        # Disconnect from database
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(initialize_project_status())