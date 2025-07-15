# Project Management Guide

This guide explains how to track project progress, manage tasks, and monitor the development status of the Video Intelligence Platform.

## Table of Contents
- [Overview](#overview)
- [Project Status Tracking](#project-status-tracking)
- [Technical Debt Management](#technical-debt-management)
- [MongoDB Collections](#mongodb-collections)
- [Management Scripts](#management-scripts)
- [Common Workflows](#common-workflows)
- [Query Commands](#query-commands)

## Overview

The Video Intelligence Platform uses MongoDB to track:
1. **Project Status**: Current phase, component completion, tasks
2. **Technical Debt**: Incomplete implementations, TODOs, production readiness issues
3. **Processing Jobs**: Video analysis job tracking
4. **Development Progress**: Metrics and milestones

## Project Status Tracking

### Understanding Project Phases

The project follows these implementation phases:

1. **SETUP** - Initial project setup
2. **FOUNDATION** - Core infrastructure (MongoDB, Celery, providers)
3. **KNOWLEDGE_EXTRACTION** - Video analysis and knowledge graph
4. **EMBEDDINGS** - Vector embeddings and semantic search
5. **RAG_IMPLEMENTATION** - Retrieval-augmented generation
6. **CONVERSATION_ENGINE** - Real-time conversational AI
7. **OPTIMIZATION** - Performance and cost optimization
8. **PRODUCTION** - Production deployment

### Checking Current Status

```bash
# View current project status
source venv/bin/activate
python scripts/init_project_status.py
```

Output shows:
- Current phase
- Component completion status (✅ completed, ⏳ in progress, ❌ not started)
- Number of completed tasks
- Current active tasks
- Latest notes

### Updating Project Status

```bash
# Update status after completing work
python scripts/update_project_status.py
```

The update script should be modified to:
- Mark components as completed/in-progress
- Add completed tasks
- Update current tasks
- Add notes about significant changes

## Technical Debt Management

### What We Track

Technical debt items are categorized by:

**Severity Levels:**
- `CRITICAL` - Security vulnerabilities, data loss risks
- `HIGH` - Core functionality blockers
- `MEDIUM` - Performance issues, missing features
- `LOW` - Code quality, documentation

**Categories:**
- `security` - Authentication, authorization, data protection
- `incomplete` - Partially implemented features
- `missing_integration` - Required services not integrated
- `hardcoded` - Values that should be configurable
- `performance` - Optimization opportunities
- `testing` - Missing test coverage
- `documentation` - Missing or outdated docs
- `error_handling` - Insufficient error handling
- `configuration` - Configuration management issues
- `monitoring` - Missing observability

### Viewing Technical Debt

```bash
# View current technical debt report
python scripts/init_technical_debt.py
```

Report includes:
- Total items and open items
- Critical and high priority counts
- Estimated hours remaining
- Items by severity and category
- Recently updated items

### Adding Technical Debt

When you encounter incomplete implementations or TODOs:

1. **In Code**: Add a comment with debt ID
```python
# TODO: [DEBT-ID] - Brief description
# See technical debt tracking for full details
```

2. **In Database**: Update the technical debt script to add the item

### Resolving Technical Debt

```bash
# Update debt status after fixing issues
python scripts/update_technical_debt.py
```

Mark items as:
- `RESOLVED` - Completely fixed
- `IN_PROGRESS` - Partially addressed
- `DEFERRED` - Postponed with reason
- `WON_T_FIX` - Decided not to fix

## MongoDB Collections

### Project Management Collections

1. **project_status**
   - Tracks overall project progress
   - Current phase and component statuses
   - Task lists and notes
   - Single document per project

2. **technical_debt**
   - All technical debt items
   - Grouped by component/service
   - Includes severity, effort estimates, and resolution status
   - Single document with nested items

### Application Collections

3. **videos**
   - Video metadata and processing status
   - References to scenes and analysis results

4. **scenes**
   - Video scenes with shots and analysis
   - Timestamps and descriptions
   - Provider-specific results

5. **processing_jobs**
   - Async job tracking
   - Progress and status updates
   - Error information

6. **knowledge_graph_nodes**
   - Entities and relationships
   - Extracted knowledge representation

## Management Scripts

All scripts are in the `scripts/` directory:

### Project Status Scripts

**`init_project_status.py`**
- Creates or displays current project status
- Run anytime to check progress
- Safe to run multiple times

**`update_project_status.py`**
- Updates project status after completing work
- Modify the script to add your updates
- Tracks completed tasks and component changes

### Technical Debt Scripts

**`init_technical_debt.py`**
- Creates or displays technical debt report
- Shows all debt items with statistics
- Groups by severity and category

**`update_technical_debt.py`**
- Updates debt item statuses
- Add new debt items
- Mark items as resolved

### Usage Examples

```bash
# Start of day - check status
source venv/bin/activate
python scripts/init_project_status.py
python scripts/init_technical_debt.py

# After completing a component
# Edit update_project_status.py to add your changes
python scripts/update_project_status.py

# After fixing technical debt
# Edit update_technical_debt.py to mark resolved
python scripts/update_technical_debt.py
```

## Common Workflows

### Starting a New Feature

1. Check current status and prerequisites
```bash
python scripts/init_project_status.py
./dev-cli ask "Prerequisites for [feature]"
```

2. Review related technical debt
```bash
python scripts/init_technical_debt.py | grep -A5 "[component]"
```

3. Implement the feature

4. Update project status
```bash
# Edit and run update_project_status.py
```

5. Check for new technical debt
```bash
# If you added TODOs, update init_technical_debt.py
```

### Fixing Technical Debt

1. Query specific debt items
```bash
python scripts/init_technical_debt.py | grep -A10 "HIGH"
```

2. Choose an item to fix (preferably blocking current work)

3. Implement the fix

4. Update debt status
```bash
# Edit and run update_technical_debt.py
```

### Daily Status Check

```bash
# Morning routine
source venv/bin/activate

# Check project progress
python scripts/init_project_status.py

# Check high-priority debt
python scripts/init_technical_debt.py | head -30

# Query knowledge base for today's work
./dev-cli ask "What should I work on next?"
```

## Query Commands

### Direct MongoDB Queries

```bash
# Access MongoDB directly
docker compose exec mongodb mongosh video_intelligence

# In MongoDB shell:
# View project status
db.project_status.findOne()

# View technical debt summary
db.technical_debt.findOne({}, {summary: 1})

# Count open processing jobs
db.processing_jobs.countDocuments({status: "in_progress"})
```

### Knowledge Base Queries

```bash
# Query implementation patterns
./dev-cli ask "How to implement [feature]"

# Get suggestions
./dev-cli suggest "[component]"

# Check for known issues
./dev-cli ask "Issues with [component]"
```

### Python Query Examples

```python
# Quick status check from Python
from backend.models import ProjectStatus, TechnicalDebt
from backend.core.database import init_database

async def check_status():
    await init_database()
    
    # Get project status
    status = await ProjectStatus.find_one()
    print(f"Current phase: {status.current_phase}")
    print(f"Completed tasks: {len(status.completed_tasks)}")
    
    # Get technical debt
    debt = await TechnicalDebt.find_one()
    report = debt.generate_report()
    print(f"Open debt items: {report['summary']['open_items']}")
    print(f"Critical items: {report['summary']['critical_items']}")
```

## Best Practices

1. **Update Regularly**: Run status updates after completing significant work
2. **Track All Debt**: Don't let TODOs hide in code comments
3. **Prioritize Blockers**: Fix technical debt that blocks current work
4. **Document Decisions**: Add notes explaining why debt was deferred
5. **Review Weekly**: Check overall progress and debt trends

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB is running
docker compose ps mongodb

# Restart if needed
docker compose restart mongodb

# Check logs
docker compose logs mongodb
```

### Script Errors
- Ensure virtual environment is activated
- Check MongoDB is accessible
- Verify you're in the project root directory

### Missing Data
- Run init scripts to create collections
- Check if documents were accidentally deleted
- Restore from git history if needed

## Related Documentation

- [Technical Debt Details](./TECHNICAL_DEBT.md) - Deep dive into debt tracking
- [Developer Onboarding](./DEVELOPER_ONBOARDING.md) - Getting started guide
- [Scripts README](../scripts/README.md) - Detailed script documentation
- [PRD](./new/video-intelligence-prd.md) - Project requirements and phases