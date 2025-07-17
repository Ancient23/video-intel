# Get Next Implementation Task

## Description
Determine what to implement next based on current progress and priorities.

## When to Use
- After completing a task
- When starting a new work session
- When blocked on current task
- During sprint planning

## Prerequisites
- Current project status known
- Understanding of project phases
- Access to technical debt tracking

## Steps

1. Check current project status in MongoDB:
   ```bash
   python scripts/init_project_status.py
   ```

2. Review PRD implementation phases:
   - Current phase requirements
   - Dependencies between components
   - Critical path items

3. **MANDATORY** Query Graph-RAG for prerequisites and patterns:
   ```bash
   # Search for implementation guidance
   ./dev-cli search "[next component] prerequisites"
   ./dev-cli search "[next component] implementation order"
   
   # Explore component relationships
   ./dev-cli explore "[next component]" --depth 2
   
   # Ask specific questions
   ./dev-cli ask "Prerequisites for [next component]"
   ./dev-cli ask "NVIDIA Blueprint patterns for [next component]"
   ```

4. Consider these factors:
   - Dependencies between components
   - Current phase objectives
   - Blocked tasks that can be unblocked
   - Quick wins vs complex tasks
   - Technical debt that blocks features
   - Team priorities

5. Recommend next task with:
   - Clear requirements and scope
   - Estimated effort (hours/days)
   - Required knowledge/patterns
   - Success criteria
   - Potential blockers

## Decision Matrix

| Priority | Type | Examples |
|----------|------|----------|
| P0 | Critical blockers | Authentication, core APIs |
| P1 | Phase requirements | Current phase components |
| P2 | Debt blocking features | Missing integrations |
| P3 | Performance/quality | Optimization, testing |
| P4 | Nice-to-have | Documentation, refactoring |

## Example Output
```
Next Recommended Task: API-Celery Integration

Priority: P1 (Phase requirement)
Component: api_endpoints
Estimated Effort: 4 hours

Prerequisites:
- ✅ Celery configuration (completed)
- ✅ API endpoints (completed)
- ✅ MongoDB models (completed)

Task Details:
1. Connect API endpoints to Celery tasks
2. Update _trigger_analysis_pipeline()
3. Add progress tracking
4. Test async processing

Success Criteria:
- Video analysis runs asynchronously
- Progress updates in MongoDB
- Proper error handling
- All tests passing

Blocks Resolution:
- Unblocks: Full video processing pipeline
- Resolves: Technical debt API-002
```

## Example Usage
```bash
# Get next task recommendation
./dev-cli prompt next-task

# With context about specific area
./dev-cli ask "What should I work on next for video processing?"
```

## Related Prompts
- `status-check` - Review current status first
- `debt-check` - Consider high-priority debt
- `impl-plan` - Plan the implementation approach