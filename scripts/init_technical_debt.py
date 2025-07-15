#!/usr/bin/env python3
"""Initialize technical debt tracking with current known issues"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "services"))

from backend.core.database import init_database, Database
from backend.models import (
    TechnicalDebt, TechnicalDebtItem, 
    DebtSeverity, DebtCategory, DebtStatus
)


async def initialize_technical_debt():
    """Create or update technical debt tracking document"""
    
    # Connect to database
    await init_database()
    
    try:
        # Check if technical debt document already exists
        tech_debt = await TechnicalDebt.find_one({"project_name": "video-intelligence-platform"})
        
        if not tech_debt:
            print("Creating new technical debt document...")
            tech_debt = TechnicalDebt()
            await tech_debt.create()
        else:
            print("Found existing technical debt document, updating...")
        
        # Define all known technical debt items
        debt_items = [
            # Authentication & Security
            {
                "component": "core/security",
                "item": TechnicalDebtItem(
                    id="SEC-001",
                    title="Placeholder Authentication Implementation",
                    description="Authentication returns hardcoded dummy user. Need to implement proper JWT validation, user management, and role-based access control.",
                    file_path="services/backend/core/deps.py",
                    line_numbers=[26, 34],
                    category=DebtCategory.SECURITY,
                    severity=DebtSeverity.CRITICAL,
                    estimated_effort_hours=16.0,
                    tags=["authentication", "jwt", "security"]
                )
            },
            
            # Missing Celery Infrastructure
            {
                "component": "workers/celery",
                "item": TechnicalDebtItem(
                    id="INFRA-001",
                    title="Missing Celery Configuration",
                    description="No celery_app.py configuration file. Background tasks using FastAPI basic background_tasks instead of proper Celery queue.",
                    file_path="services/backend/workers/",
                    category=DebtCategory.MISSING_INTEGRATION,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=8.0,
                    tags=["celery", "infrastructure", "async"]
                )
            },
            
            # S3 Download Not Implemented
            {
                "component": "providers/nvidia",
                "item": TechnicalDebtItem(
                    id="PROV-001",
                    title="NVIDIA VILA S3 Download Not Implemented",
                    description="S3 download functionality raises NotImplementedError. Provider cannot process videos from S3.",
                    file_path="services/backend/services/analysis/providers/nvidia_vila.py",
                    line_numbers=[80, 81],
                    category=DebtCategory.INCOMPLETE,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=4.0,
                    tags=["s3", "provider", "nvidia"]
                )
            },
            
            # Missing Core Services
            {
                "component": "services/embeddings",
                "item": TechnicalDebtItem(
                    id="CORE-001",
                    title="Missing Embeddings Service",
                    description="Vector embeddings service not implemented. Required for semantic search and RAG functionality.",
                    category=DebtCategory.MISSING_INTEGRATION,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=24.0,
                    tags=["embeddings", "rag", "core-service"]
                )
            },
            {
                "component": "services/knowledge_graph",
                "item": TechnicalDebtItem(
                    id="CORE-002",
                    title="Missing Knowledge Graph Service",
                    description="Knowledge graph construction service not implemented. Required for relationship mapping and graph-based queries.",
                    category=DebtCategory.MISSING_INTEGRATION,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=32.0,
                    tags=["knowledge-graph", "core-service"]
                )
            },
            {
                "component": "services/rag",
                "item": TechnicalDebtItem(
                    id="CORE-003",
                    title="Missing RAG System",
                    description="Retrieval-augmented generation system not implemented. Core requirement for conversational AI.",
                    category=DebtCategory.MISSING_INTEGRATION,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=40.0,
                    tags=["rag", "core-service", "ai"]
                )
            },
            
            # Configuration Management
            {
                "component": "core/config",
                "item": TechnicalDebtItem(
                    id="CONFIG-001",
                    title="No Centralized Configuration Management",
                    description="Environment variables accessed directly without validation. No Pydantic settings class or .env.example file.",
                    category=DebtCategory.CONFIGURATION,
                    severity=DebtSeverity.MEDIUM,
                    estimated_effort_hours=6.0,
                    tags=["configuration", "environment"]
                )
            },
            {
                "component": "api/security",
                "item": TechnicalDebtItem(
                    id="CONFIG-002",
                    title="CORS Allows All Origins",
                    description="CORS configured with allow_origins=['*'] which is insecure for production.",
                    file_path="services/backend/main.py",
                    line_numbers=[67],
                    category=DebtCategory.SECURITY,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=2.0,
                    tags=["cors", "security", "configuration"]
                )
            },
            
            # Vector Database Integration
            {
                "component": "database/vector",
                "item": TechnicalDebtItem(
                    id="DB-001",
                    title="No Vector Database Integration",
                    description="Milvus or Pinecone integration not implemented despite PRD requirements. VECTOR_DB_TYPE env var referenced but unused.",
                    category=DebtCategory.MISSING_INTEGRATION,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=16.0,
                    tags=["vector-db", "database", "integration"]
                )
            },
            
            # Redis Cache Missing
            {
                "component": "utils/cache",
                "item": TechnicalDebtItem(
                    id="CACHE-001",
                    title="Redis Cache Utilities Not Implemented",
                    description="Redis caching utilities referenced in tests but not implemented. Need cache_utils.py from VideoCommentator.",
                    category=DebtCategory.MISSING_INTEGRATION,
                    severity=DebtSeverity.MEDIUM,
                    estimated_effort_hours=4.0,
                    tags=["redis", "cache", "performance"]
                )
            },
            
            # Hardcoded Values
            {
                "component": "providers/aws",
                "item": TechnicalDebtItem(
                    id="HARD-001",
                    title="Hardcoded Retry Limits in AWS Provider",
                    description="Max retry attempts hardcoded to 60. Should be configurable.",
                    file_path="services/backend/services/analysis/providers/aws_rekognition.py",
                    line_numbers=[217],
                    category=DebtCategory.HARDCODED,
                    severity=DebtSeverity.LOW,
                    estimated_effort_hours=1.0,
                    tags=["hardcoded", "configuration"]
                )
            },
            {
                "component": "providers/nvidia",
                "item": TechnicalDebtItem(
                    id="HARD-002",
                    title="Hardcoded Model Temperature",
                    description="Temperature parameter hardcoded to 0.7. Should be configurable per request.",
                    file_path="services/backend/services/analysis/providers/nvidia_vila.py",
                    line_numbers=[139],
                    category=DebtCategory.HARDCODED,
                    severity=DebtSeverity.LOW,
                    estimated_effort_hours=1.0,
                    tags=["hardcoded", "ai-model"]
                )
            },
            
            # API Implementation
            {
                "component": "api/video_analysis",
                "item": TechnicalDebtItem(
                    id="API-001",
                    title="Video Analysis Pipeline is Stub Implementation",
                    description="_trigger_analysis_pipeline() only prints to console. No actual Celery task triggering.",
                    file_path="services/backend/api/v1/routers/video_analysis.py",
                    line_numbers=[573, 580],
                    category=DebtCategory.INCOMPLETE,
                    severity=DebtSeverity.HIGH,
                    estimated_effort_hours=4.0,
                    tags=["api", "incomplete", "celery"]
                )
            },
            
            # Testing Infrastructure
            {
                "component": "tests/integration",
                "item": TechnicalDebtItem(
                    id="TEST-001",
                    title="No Integration Tests",
                    description="Tests heavily rely on mocks. No integration tests for S3, vector DB, or external APIs.",
                    category=DebtCategory.TESTING,
                    severity=DebtSeverity.MEDIUM,
                    estimated_effort_hours=20.0,
                    tags=["testing", "integration-tests"]
                )
            },
            
            # Monitoring & Observability
            {
                "component": "core/monitoring",
                "item": TechnicalDebtItem(
                    id="MON-001",
                    title="No Monitoring or Health Checks",
                    description="No metrics collection, distributed tracing, or health checks for dependencies (MongoDB, Redis, S3).",
                    category=DebtCategory.MONITORING,
                    severity=DebtSeverity.MEDIUM,
                    estimated_effort_hours=12.0,
                    tags=["monitoring", "observability", "health-checks"]
                )
            },
            
            # NLP Parsing
            {
                "component": "providers/nvidia",
                "item": TechnicalDebtItem(
                    id="ALGO-001",
                    title="Simple NLP Parsing in NVIDIA Provider",
                    description="Scene extraction uses simple string parsing. Should use more sophisticated NLP.",
                    file_path="services/backend/services/analysis/providers/nvidia_vila.py",
                    line_numbers=[213],
                    category=DebtCategory.PERFORMANCE,
                    severity=DebtSeverity.LOW,
                    estimated_effort_hours=8.0,
                    tags=["nlp", "parsing", "ai"]
                )
            },
            
            # AWS Configuration
            {
                "component": "providers/aws",
                "item": TechnicalDebtItem(
                    id="AWS-001",
                    title="AWS Role ARN Configuration Without Validation",
                    description="AWS Rekognition Role ARN and SNS topic from env vars without validation.",
                    file_path="services/backend/services/analysis/providers/aws_rekognition.py",
                    line_numbers=[95, 97],
                    category=DebtCategory.CONFIGURATION,
                    severity=DebtSeverity.MEDIUM,
                    estimated_effort_hours=2.0,
                    tags=["aws", "configuration", "validation"]
                )
            },
        ]
        
        # Add all debt items
        for debt_dict in debt_items:
            tech_debt.add_debt_item(debt_dict["component"], debt_dict["item"])
        
        # Save the document
        await tech_debt.save()
        
        # Generate and print report
        report = tech_debt.generate_report()
        
        print("\n=== Technical Debt Report ===")
        print(f"Project: {tech_debt.project_name}")
        print(f"Last Updated: {tech_debt.updated_at}")
        
        print("\nSummary:")
        for key, value in report["summary"].items():
            print(f"  {key}: {value}")
        
        print("\nBy Severity:")
        for severity in ["critical", "high", "medium", "low"]:
            items = report["by_severity"][severity]
            if items:
                print(f"  {severity.upper()}: {len(items)} items")
                for item in items[:3]:  # Show first 3
                    print(f"    - [{item['id']}] {item['title']}")
        
        print("\nBy Category:")
        for category, count in report["by_category"].items():
            print(f"  {category}: {count} items")
        
        print("\nTop Priority Items:")
        critical_items = tech_debt.get_debt_by_severity(DebtSeverity.CRITICAL)
        for item in critical_items:
            print(f"  - [{item.id}] {item.title}")
            print(f"    Effort: {item.estimated_effort_hours}h")
        
        print(f"\n✅ Technical debt tracking initialized with {tech_debt.total_items} items!")
        
    except Exception as e:
        print(f"❌ Error initializing technical debt: {e}")
        raise
    finally:
        # Disconnect from database
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(initialize_technical_debt())