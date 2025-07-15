# Scripts Documentation

This directory contains management scripts for the Video Intelligence Platform. These scripts help track project progress, manage technical debt, and maintain project health.

## Table of Contents
- [Overview](#overview)
- [Project Status Scripts](#project-status-scripts)
- [Technical Debt Scripts](#technical-debt-scripts)
- [Usage Examples](#usage-examples)
- [Creating New Scripts](#creating-new-scripts)
- [Best Practices](#best-practices)

## Overview

All scripts are Python-based and require the virtual environment to be activated:

```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

Scripts connect to MongoDB to read/write project management data. Ensure MongoDB is running:

```bash
docker compose up -d mongodb
```

## Project Status Scripts

### init_project_status.py

**Purpose**: Initialize or display current project status

**Usage**:
```bash
python scripts/init_project_status.py
```

**What it does**:
- Creates project status document if it doesn't exist
- Displays current phase and progress
- Shows component completion status
- Lists completed and current tasks
- Safe to run multiple times (idempotent)

**Output Example**:
```
=== Project Status ===
Project: video-intelligence-platform
Phase: ProjectPhase.FOUNDATION
Updated: 2024-01-15 10:30:00

Component Status:
  ✅ mongodb_setup: ComponentStatus.COMPLETED
  ✅ video_chunking: ComponentStatus.COMPLETED
  ⏳ api_endpoints: ComponentStatus.IN_PROGRESS
  ❌ knowledge_graph: ComponentStatus.NOT_STARTED

Completed Tasks: 15
Current Tasks: 5

Latest Note:
  [implementation] Completed video chunking service
```

### update_project_status.py

**Purpose**: Update project status after completing work

**Usage**:
1. Edit the script to add your updates
2. Run: `python scripts/update_project_status.py`

**How to modify**:
```python
# Update component status
status.update_component("api_endpoints", ComponentStatus.COMPLETED)

# Add completed tasks
new_completed_tasks = [
    "Implement user authentication",
    "Add rate limiting to API",
    "Create API documentation"
]
for task in new_completed_tasks:
    status.add_completed_task(task)

# Update current tasks
status.current_tasks = [
    "Implement knowledge graph construction",
    "Create embedding service"
]

# Add a note
status.add_note("Completed API implementation with auth", "implementation")
```

## Technical Debt Scripts

### init_technical_debt.py

**Purpose**: Initialize or display technical debt report

**Usage**:
```bash
python scripts/init_technical_debt.py
```

**What it does**:
- Creates technical debt tracking document
- Displays comprehensive debt report
- Shows items by severity and category
- Calculates total estimated effort
- Lists high-priority items

**Output Example**:
```
=== Technical Debt Report ===
Project: video-intelligence-platform
Last Updated: 2024-01-15 11:00:00

Summary:
  total_items: 19
  open_items: 16
  critical_items: 1
  high_priority_items: 10
  estimated_hours_remaining: 198.0

By Severity:
  CRITICAL: 1 items
    - [SEC-001] Placeholder Authentication Implementation
  HIGH: 10 items
    - [API-002] API Endpoints Need Celery Task Integration
    - [PROV-001] NVIDIA VILA S3 Download Not Implemented
```

**Adding new debt items**:

Edit the script to add items to the `debt_items` list:

```python
debt_items = [
    {
        "component": "api/endpoints",
        "item": TechnicalDebtItem(
            id="API-003",
            title="Missing Rate Limiting",
            description="API endpoints have no rate limiting, could be abused",
            file_path="services/backend/api/v1/routers/video_analysis.py",
            line_numbers=[50, 75],
            category=DebtCategory.SECURITY,
            severity=DebtSeverity.HIGH,
            estimated_effort_hours=8.0,
            tags=["api", "security", "rate-limiting"]
        )
    }
]
```

### update_technical_debt.py

**Purpose**: Update technical debt status after resolving issues

**Usage**:
1. Edit the script to add your updates
2. Run: `python scripts/update_technical_debt.py`

**Marking items as resolved**:
```python
resolved_items = [
    {
        "component": "api/endpoints",
        "item_id": "API-003",
        "resolution": "Implemented rate limiting using slowapi with Redis backend"
    }
]
```

**Updating item status**:
```python
# Mark as in progress
tech_debt.update_debt_status(
    "api/endpoints",
    "API-003",
    DebtStatus.IN_PROGRESS,
    "Started implementation, 50% complete"
)
```

## Usage Examples

### Daily Workflow

```bash
# Morning: Check status
source venv/bin/activate
python scripts/init_project_status.py
python scripts/init_technical_debt.py | head -40

# After completing work
# Edit update_project_status.py with your changes
python scripts/update_project_status.py

# If you fixed technical debt
# Edit update_technical_debt.py
python scripts/update_technical_debt.py
```

### Weekly Review

```bash
# Generate full reports
python scripts/init_project_status.py > reports/status_$(date +%Y%m%d).txt
python scripts/init_technical_debt.py > reports/debt_$(date +%Y%m%d).txt

# Track progress
git add reports/
git commit -m "Weekly status reports"
```

### Filtering Output

```bash
# Show only high-priority debt
python scripts/init_technical_debt.py | grep -A10 "HIGH\|CRITICAL"

# Show specific component status
python scripts/init_project_status.py | grep -A5 "api_endpoints"

# Count open items by category
python scripts/init_technical_debt.py | grep "items" | sort | uniq -c
```

## Creating New Scripts

### Template for New Management Script

```python
#!/usr/bin/env python3
"""Description of what this script does"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "services"))

from backend.core.database import init_database, Database
from backend.models import YourModel


async def main():
    """Main function description"""
    
    # Connect to database
    await init_database()
    
    try:
        # Your logic here
        document = await YourModel.find_one({"field": "value"})
        
        if not document:
            print("Creating new document...")
            document = YourModel(field="value")
            await document.create()
        
        # Process and display
        print(f"Result: {document.field}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Always disconnect
        await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
```

### Making Scripts Executable

```bash
chmod +x scripts/your_new_script.py
```

### Adding Script Documentation

Update this README.md with:
1. Script name and purpose
2. Usage instructions
3. Example output
4. Common modifications

## Best Practices

### 1. Idempotency
Scripts should be safe to run multiple times:
```python
# Check if exists before creating
existing = await Model.find_one({"identifier": "value"})
if not existing:
    # Create new
else:
    # Update existing
```

### 2. Clear Output
Use visual indicators:
```python
print("✅ Success message")
print("❌ Error message")
print("⏳ In progress")
print("⚠️  Warning")
```

### 3. Error Handling
Always wrap in try-except:
```python
try:
    # Database operations
except Exception as e:
    print(f"❌ Error: {e}")
    raise
finally:
    await Database.disconnect()
```

### 4. Timestamps
Use timezone-aware datetime:
```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### 5. Progress Indicators
For long operations:
```python
total = len(items)
for i, item in enumerate(items):
    print(f"Processing {i+1}/{total}: {item.name}")
    # Process item
```

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker compose ps mongodb

# View logs
docker compose logs mongodb

# Restart
docker compose restart mongodb
```

### Import Errors
```bash
# Ensure virtual environment is activated
which python

# Verify backend is in path
python -c "import sys; print('\n'.join(sys.path))"
```

### Script Permissions
```bash
# Make executable
chmod +x scripts/*.py

# Run with Python explicitly
python scripts/script_name.py
```

## Future Scripts

Planned scripts to be added:
- `export_metrics.py` - Export project metrics
- `backup_status.py` - Backup project state
- `generate_report.py` - Create formatted reports
- `migrate_data.py` - Handle schema migrations
- `cleanup_debt.py` - Archive resolved debt items