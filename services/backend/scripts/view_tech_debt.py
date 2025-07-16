#!/usr/bin/env python
"""
View current technical debt and project status
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.database import Database
from models import TechnicalDebt, ProjectStatus, DebtSeverity


async def view_technical_debt():
    """View current technical debt from MongoDB"""
    # Connect to database
    await Database.connect()
    
    try:
        # Find technical debt document
        tech_debt = await TechnicalDebt.find_one(
            TechnicalDebt.project_name == "video-intelligence-platform"
        )
        
        if not tech_debt:
            print("No technical debt document found")
            return
        
        print("=== TECHNICAL DEBT TRACKING ===")
        print(f"Last Updated: {tech_debt.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nSummary:")
        print(f"  Total Items: {tech_debt.total_items}")
        print(f"  Open Items: {tech_debt.open_items}")
        print(f"  Critical Items: {tech_debt.critical_items}")
        print(f"  High Priority Items: {tech_debt.high_priority_items}")
        print(f"  Estimated Hours: {tech_debt.total_estimated_hours}")
        
        print("\nHIGH PRIORITY ITEMS:")
        high_items = tech_debt.get_debt_by_severity(DebtSeverity.HIGH)
        for item in high_items:
            print(f"\n  [{item.id}] {item.title}")
            print(f"  Category: {item.category.value}")
            print(f"  Estimated Hours: {item.estimated_effort_hours}")
            print(f"  Description: {item.description[:100]}...")
            if item.file_path:
                print(f"  File: {item.file_path}")
        
        print("\nMEDIUM PRIORITY ITEMS:")
        medium_items = tech_debt.get_debt_by_severity(DebtSeverity.MEDIUM)
        for item in medium_items[:3]:  # Show first 3
            print(f"\n  [{item.id}] {item.title}")
            print(f"  Category: {item.category.value}")
            print(f"  Estimated Hours: {item.estimated_effort_hours}")
        
        print("\nLOW PRIORITY ITEMS:")
        low_items = tech_debt.get_debt_by_severity(DebtSeverity.LOW)
        for item in low_items:
            print(f"  - [{item.id}] {item.title} ({item.estimated_effort_hours}h)")
        
    finally:
        await Database.disconnect()


async def view_project_status():
    """View current project status from MongoDB"""
    # Connect to database
    await Database.connect()
    
    try:
        # Find project status
        status = await ProjectStatus.find_one(
            ProjectStatus.project_name == "video-intelligence-platform"
        )
        
        if not status:
            print("No project status document found")
            return
        
        print("\n\n=== PROJECT STATUS ===")
        print(f"Current Phase: {status.current_phase.value}")
        print(f"Last Updated: {status.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Coverage: {status.test_coverage}%")
        
        print("\nComponent Status:")
        for component, comp_status in status.components.items():
            symbol = "✅" if comp_status.value == "completed" else "⏳" if comp_status.value == "in_progress" else "❌"
            print(f"  {symbol} {component}: {comp_status.value}")
        
        print(f"\nCompleted Tasks ({len(status.completed_tasks)}):")
        for task in status.completed_tasks[-5:]:  # Show last 5
            print(f"  ✓ {task}")
        
        print(f"\nCurrent Tasks ({len(status.current_tasks)}):")
        for task in status.current_tasks:
            print(f"  → {task}")
        
        if status.known_issues:
            print(f"\nKnown Issues ({len(status.known_issues)}):")
            for issue in status.known_issues:
                print(f"  ⚠️  [{issue['severity']}] {issue['issue']} ({issue['component']})")
        
    finally:
        await Database.disconnect()


async def main():
    """Main function to view all tracking data"""
    await view_technical_debt()
    await view_project_status()


if __name__ == "__main__":
    asyncio.run(main())