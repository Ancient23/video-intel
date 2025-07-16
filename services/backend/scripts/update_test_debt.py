#!/usr/bin/env python
"""
Update technical debt tracking with test execution findings
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.database import Database
from models import (
    TechnicalDebt, TechnicalDebtItem, DebtSeverity, 
    DebtCategory, DebtStatus, ProjectStatus, ComponentStatus
)


async def create_debt_items() -> List[Dict[str, TechnicalDebtItem]]:
    """Create technical debt items from test execution findings"""
    
    debt_items = {
        "api": [
            TechnicalDebtItem(
                id="api-001",
                title="API endpoints for video analysis not implemented",
                description="Integration tests are failing because video analysis endpoints are empty shells. Need to implement full CRUD operations for video analysis jobs.",
                file_path="/services/backend/api/v1/videos.py",
                category=DebtCategory.INCOMPLETE,
                severity=DebtSeverity.HIGH,
                estimated_effort_hours=16.0,
                tags=["api", "video-analysis", "integration-tests"]
            ),
            TechnicalDebtItem(
                id="api-002",
                title="Authentication system not implemented",
                description="API tests require authentication but the auth system is not implemented. Need JWT-based auth with user roles.",
                file_path="/services/backend/api/auth/",
                category=DebtCategory.MISSING_INTEGRATION,
                severity=DebtSeverity.MEDIUM,
                estimated_effort_hours=24.0,
                tags=["api", "authentication", "security"]
            ),
        ],
        "models": [
            TechnicalDebtItem(
                id="models-001",
                title="VideoAnalysisJob model needs full implementation",
                description="Current model is a stub. Need to add all fields for tracking analysis progress, results, and provider metadata.",
                file_path="/services/backend/models/video_analysis_job.py",
                category=DebtCategory.INCOMPLETE,
                severity=DebtSeverity.HIGH,
                estimated_effort_hours=8.0,
                tags=["models", "video-analysis", "database"]
            ),
        ],
        "workers": [
            TechnicalDebtItem(
                id="workers-001",
                title="Worker tasks are empty shells",
                description="Celery tasks for video processing are not implemented. Need chunking, analysis, and knowledge graph construction tasks.",
                file_path="/services/backend/workers/tasks/",
                category=DebtCategory.INCOMPLETE,
                severity=DebtSeverity.HIGH,
                estimated_effort_hours=40.0,
                tags=["workers", "celery", "video-processing"]
            ),
        ],
        "testing": [
            TechnicalDebtItem(
                id="testing-001",
                title="Test coverage at 25% - needs to be 80%+",
                description="Current test coverage is too low. Need comprehensive unit tests for all services and integration tests for workflows.",
                category=DebtCategory.TESTING,
                severity=DebtSeverity.MEDIUM,
                estimated_effort_hours=32.0,
                tags=["testing", "coverage", "quality"]
            ),
            TechnicalDebtItem(
                id="testing-002",
                title="No E2E workflow tests",
                description="Missing end-to-end tests for complete video processing workflows. Need tests that verify the entire pipeline.",
                category=DebtCategory.TESTING,
                severity=DebtSeverity.MEDIUM,
                estimated_effort_hours=16.0,
                tags=["testing", "e2e", "workflows"]
            ),
            TechnicalDebtItem(
                id="testing-003",
                title="No performance benchmarks",
                description="Need performance benchmarks to track processing speed and resource usage across different video sizes.",
                category=DebtCategory.PERFORMANCE,
                severity=DebtSeverity.LOW,
                estimated_effort_hours=8.0,
                tags=["testing", "performance", "benchmarks"]
            ),
            TechnicalDebtItem(
                id="testing-004",
                title="No load testing framework",
                description="Need load testing to ensure the system can handle concurrent video processing requests.",
                category=DebtCategory.TESTING,
                severity=DebtSeverity.LOW,
                estimated_effort_hours=12.0,
                tags=["testing", "load-testing", "scalability"]
            ),
            TechnicalDebtItem(
                id="testing-005",
                title="Need test data factories",
                description="Current tests use hardcoded data. Need factories for generating test videos, scenes, and analysis results.",
                category=DebtCategory.TESTING,
                severity=DebtSeverity.LOW,
                estimated_effort_hours=8.0,
                tags=["testing", "factories", "test-data"]
            ),
        ],
    }
    
    return debt_items


async def update_technical_debt():
    """Update technical debt tracking in MongoDB"""
    # Connect to database
    await Database.connect()
    
    try:
        # Find or create technical debt document
        tech_debt = await TechnicalDebt.find_one(
            TechnicalDebt.project_name == "video-intelligence-platform"
        )
        
        if not tech_debt:
            tech_debt = TechnicalDebt()
            print("Created new technical debt document")
        else:
            print("Found existing technical debt document")
        
        # Create debt items
        debt_items = await create_debt_items()
        
        # Add all debt items
        for component, items in debt_items.items():
            for item in items:
                tech_debt.add_debt_item(component, item)
                print(f"Added debt item: {item.id} - {item.title}")
        
        # Save to database
        await tech_debt.save()
        
        # Generate and print report
        report = tech_debt.generate_report()
        print("\n=== Technical Debt Report ===")
        print(f"Total items: {report['summary']['total_items']}")
        print(f"Open items: {report['summary']['open_items']}")
        print(f"Critical items: {report['summary']['critical_items']}")
        print(f"High priority items: {report['summary']['high_priority_items']}")
        print(f"Estimated hours remaining: {report['summary']['estimated_hours_remaining']}")
        
        print("\nBy Severity:")
        for severity, items in report['by_severity'].items():
            if items:
                print(f"  {severity.upper()}: {len(items)} items")
                for item in items[:3]:  # Show first 3
                    print(f"    - {item['title'][:60]}...")
        
        print("\nBy Component:")
        for component, stats in report['by_component'].items():
            print(f"  {component}: {stats['open_items']} items, {stats['total_hours']} hours")
        
    finally:
        await Database.disconnect()


async def update_project_status():
    """Update project status to reflect test infrastructure completion"""
    # Connect to database
    await Database.connect()
    
    try:
        # Find or create project status
        status = await ProjectStatus.find_one(
            ProjectStatus.project_name == "video-intelligence-platform"
        )
        
        if not status:
            status = ProjectStatus()
            print("\nCreated new project status document")
        else:
            print("\nFound existing project status document")
        
        # Update test infrastructure status
        status.update_component("testing_suite", ComponentStatus.COMPLETED)
        
        # Update test coverage
        status.test_coverage = 25.0
        
        # Add completed tasks
        completed_tasks = [
            "Set up pytest infrastructure",
            "Create test categories (unit, integration, e2e)",
            "Implement test fixtures for database and services",
            "Create docker-compose test environment",
            "Set up test coverage reporting",
            "Implement infrastructure tests for Docker services",
            "Create API test framework",
            "Implement model validation tests",
        ]
        
        for task in completed_tasks:
            status.add_completed_task(task)
        
        # Update current tasks based on debt findings
        status.current_tasks = [
            "Implement video analysis API endpoints",
            "Complete VideoAnalysisJob model implementation",
            "Implement Celery worker tasks for video processing",
            "Increase test coverage to 80%+",
        ]
        
        # Add notes about test findings
        status.add_note(
            "Test infrastructure is complete and operational. Integration tests reveal "
            "that API endpoints and worker tasks need implementation.",
            category="testing"
        )
        
        status.add_note(
            "Current test coverage at 25%. Need comprehensive unit tests for all services "
            "and integration tests for complete workflows.",
            category="testing"
        )
        
        # Update known issues
        status.known_issues = [
            {
                "issue": "Integration tests failing due to unimplemented endpoints",
                "severity": "high",
                "component": "api"
            },
            {
                "issue": "Worker tasks are empty shells",
                "severity": "high", 
                "component": "workers"
            },
            {
                "issue": "Low test coverage (25%)",
                "severity": "medium",
                "component": "testing"
            },
        ]
        
        # Save to database
        await status.save()
        
        print("\n=== Project Status Updated ===")
        print(f"Testing Suite: {status.components['testing_suite'].value}")
        print(f"Test Coverage: {status.test_coverage}%")
        print(f"Completed Tasks: {len(status.completed_tasks)}")
        print(f"Current Tasks: {len(status.current_tasks)}")
        print(f"Known Issues: {len(status.known_issues)}")
        
        print("\nCurrent Tasks:")
        for task in status.current_tasks[:5]:
            print(f"  - {task}")
        
        print("\nComponent Status:")
        for component, comp_status in status.components.items():
            print(f"  {component}: {comp_status.value}")
        
    finally:
        await Database.disconnect()


async def main():
    """Main function to run all updates"""
    print("Updating technical debt tracking...")
    await update_technical_debt()
    
    print("\n" + "="*50 + "\n")
    
    print("Updating project status...")
    await update_project_status()
    
    print("\nAll updates completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())