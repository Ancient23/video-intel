#!/usr/bin/env python3
"""Update technical debt status for resolved items"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "services"))

from backend.core.database import init_database, Database
from backend.models import TechnicalDebt, DebtStatus


async def update_technical_debt():
    """Update technical debt status for resolved items"""
    
    # Connect to database
    await init_database()
    
    try:
        # Get technical debt document
        tech_debt = await TechnicalDebt.find_one({"project_name": "video-intelligence-platform"})
        
        if not tech_debt:
            print("❌ No technical debt document found!")
            return
        
        print("Updating technical debt status...")
        
        # Update resolved items
        resolved_items = [
            {
                "component": "utils/cache",
                "item_id": "CACHE-001",
                "resolution": "Copied production-tested cache utilities from VideoCommentator with extended service support"
            },
            {
                "component": "workers/celery",
                "item_id": "INFRA-001",
                "resolution": "Copied and adapted Celery configuration from VideoCommentator with two-phase architecture support"
            },
            {
                "component": "core/monitoring",
                "item_id": "MON-001",
                "resolution": "Partially resolved: Copied logging configuration and memory monitoring. Still need metrics collection and health checks."
            }
        ]
        
        # Mark items as resolved or in progress
        for resolved in resolved_items:
            if resolved["item_id"] == "MON-001":
                # Partial resolution - mark as in progress
                tech_debt.update_debt_status(
                    resolved["component"],
                    resolved["item_id"],
                    DebtStatus.IN_PROGRESS,
                    resolved["resolution"]
                )
                print(f"  ⏳ {resolved['item_id']} - Marked as IN_PROGRESS")
            else:
                tech_debt.update_debt_status(
                    resolved["component"],
                    resolved["item_id"],
                    DebtStatus.RESOLVED,
                    resolved["resolution"]
                )
                print(f"  ✅ {resolved['item_id']} - Marked as RESOLVED")
        
        # Add new debt items discovered during implementation
        new_debt_items = [
            {
                "component": "api/video_analysis",
                "item": {
                    "id": "API-002",
                    "title": "API Endpoints Need Celery Task Integration",
                    "description": "Video analysis API endpoints use placeholder background tasks. Need to integrate with actual Celery tasks.",
                    "file_path": "services/backend/api/v1/routers/video_analysis.py",
                    "line_numbers": [197, 573, 580],
                    "category": "incomplete",
                    "severity": "high",
                    "estimated_effort_hours": 4.0,
                    "tags": ["api", "celery", "integration"]
                }
            },
            {
                "component": "workers/tasks",
                "item": {
                    "id": "TASK-001",
                    "title": "Celery Tasks Need MongoDB Integration",
                    "description": "Celery tasks have placeholders for MongoDB operations. Need to implement actual database updates.",
                    "file_path": "services/backend/workers/",
                    "category": "incomplete",
                    "severity": "high",
                    "estimated_effort_hours": 6.0,
                    "tags": ["celery", "mongodb", "integration"]
                }
            }
        ]
        
        # Add new debt items
        from backend.models import TechnicalDebtItem, DebtSeverity, DebtCategory
        
        for new_debt in new_debt_items:
            item = TechnicalDebtItem(
                id=new_debt["item"]["id"],
                title=new_debt["item"]["title"],
                description=new_debt["item"]["description"],
                file_path=new_debt["item"].get("file_path"),
                line_numbers=new_debt["item"].get("line_numbers"),
                category=DebtCategory(new_debt["item"]["category"]),
                severity=DebtSeverity(new_debt["item"]["severity"]),
                estimated_effort_hours=new_debt["item"]["estimated_effort_hours"],
                tags=new_debt["item"]["tags"]
            )
            tech_debt.add_debt_item(new_debt["component"], item)
            print(f"  ⚠️  {item.id} - Added new debt item")
        
        # Save changes
        await tech_debt.save()
        
        # Generate updated report
        report = tech_debt.generate_report()
        
        print("\n=== Updated Technical Debt Report ===")
        print(f"Project: {tech_debt.project_name}")
        print(f"Last Updated: {tech_debt.updated_at}")
        
        print("\nSummary:")
        for key, value in report["summary"].items():
            print(f"  {key}: {value}")
        
        print("\nResolved Items:")
        for resolved in resolved_items:
            if resolved["item_id"] != "MON-001":
                print(f"  - [{resolved['item_id']}] {resolved['resolution']}")
        
        print("\nNew High Priority Items:")
        for severity_item in report["by_severity"]["high"]:
            if severity_item["id"] in ["API-002", "TASK-001"]:
                print(f"  - [{severity_item['id']}] {severity_item['title']}")
        
        print("\nNext Steps:")
        print("  1. Complete API-Celery integration (API-002)")
        print("  2. Implement MongoDB updates in Celery tasks (TASK-001)")  
        print("  3. Resolve NVIDIA VILA S3 download (PROV-001)")
        print("  4. Implement authentication (SEC-001)")
        
        print(f"\n✅ Technical debt updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating technical debt: {e}")
        raise
    finally:
        # Disconnect from database
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(update_technical_debt())