# MongoDB Status Update

## Description
Update project status after completing a task or component.

## When to Use
- After completing a significant feature
- When finishing a component implementation
- After resolving technical debt
- At the end of your work session

## Prerequisites
- Task or component completed
- Tests passing
- Technical debt documented if any

## Steps

1. Update MongoDB status:
   - Mark component status if applicable
   - Add completed task to list
   - Remove from current tasks
   - Add any new notes or issues

2. Check for technical debt:
   - Review code for TODO/FIXME comments
   - Identify incomplete implementations
   - Note any hardcoded values or workarounds
   - Add items to technical debt tracking:
     ```bash
     python scripts/init_technical_debt.py
     ```

3. Query knowledge base for related items:
   ```bash
   ./dev-cli ask "Any issues related to [component]?"
   ```

4. Update knowledge base if new patterns discovered:
   - Create markdown file in `dev-knowledge-base/docs/`
   - Document pattern/lesson learned
   - Run knowledge base ingestion

5. Generate report showing:
   - What was updated
   - Current phase progress
   - Any technical debt created
   - Next recommended tasks

## Update Script Template
Edit `scripts/update_project_status.py`:

```python
# Update component status
status.update_component("api_endpoints", ComponentStatus.COMPLETED)

# Add completed tasks
new_completed_tasks = [
    "Implement video analysis API endpoints",
    "Add Celery task integration",
    "Create comprehensive API tests"
]
for task in new_completed_tasks:
    status.add_completed_task(task)

# Update current tasks
status.current_tasks = [
    "Implement knowledge graph construction",
    "Create embedding service",
    "Build RAG system"
]

# Add note
status.add_note(
    "Completed API implementation with full Celery integration",
    "implementation"
)
```

## Example Usage
```bash
# After implementing a feature
./dev-cli prompt status-update

# Update both status and debt
./dev-cli prompt status-update && ./dev-cli prompt debt-add
```

## Related Prompts
- `status-check` - View current status before updating
- `debt-add` - Add technical debt discovered
- `knowledge-add` - Document new patterns