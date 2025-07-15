# Project Status Check

## Description
Check the current project status and show what needs to be done next.

## When to Use
- Starting your work session
- After completing a major task
- During weekly reviews
- When deciding what to work on next

## Prerequisites
- Virtual environment activated
- MongoDB running via Docker
- Access to dev-cli tool

## Steps

1. Query MongoDB project status:
   ```bash
   python scripts/init_project_status.py
   ```

2. Use dev-cli to check for relevant patterns:
   ```bash
   source venv/bin/activate
   ./dev-cli ask "What are the current implementation priorities?"
   ```

3. Review PRD for current phase requirements:
   - Check `/docs/new/video-intelligence-prd.md`
   - Identify current phase tasks

4. Analysis should show:
   - Current phase and progress percentage
   - Component completion status (✅/⏳/❌)
   - Active tasks with priorities
   - Blocked items with reasons
   - Next recommended steps

## Expected Output
```
=== Project Status ===
Project: video-intelligence-platform
Phase: ProjectPhase.FOUNDATION
Updated: 2024-01-15 10:30:00

Component Status:
  ✅ mongodb_setup: COMPLETED
  ✅ video_chunking: COMPLETED
  ⏳ api_endpoints: IN_PROGRESS
  ❌ knowledge_graph: NOT_STARTED

Completed Tasks: 15
Current Tasks: 5

Next Steps:
1. Complete API endpoint implementation
2. Integrate Celery tasks
3. Begin knowledge graph design
```

## Example Usage
```bash
# Quick status check
./dev-cli prompt status-check

# With technical debt analysis
./dev-cli prompt status-check && ./dev-cli prompt debt-check
```

## Related Prompts
- `status-update` - Update status after completing work
- `next-task` - Get specific task recommendations
- `debt-check` - Review technical debt alongside status