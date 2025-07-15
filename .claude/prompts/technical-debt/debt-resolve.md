# Resolve Technical Debt

## Description
Mark a technical debt item as resolved after implementing the fix.

## When to Use
- After fixing a technical debt item
- When partially resolving debt (mark as IN_PROGRESS)
- When deciding not to fix (mark as WON_T_FIX)
- After implementing workaround (mark as DEFERRED)

## Prerequisites
- Debt item ID to resolve
- Fix implemented and tested
- TODO/FIXME comments removed
- Tests added if applicable

## Input Required
- **Debt ID**: ID from technical debt tracking (e.g., API-002)
- **Resolution**: Description of how it was fixed
- **Status**: RESOLVED/IN_PROGRESS/DEFERRED/WON_T_FIX

## Steps

### Pre-Resolution

1. Query debt details:
   - Get full description and requirements
   - Check file locations
   - Review estimated effort
   
2. Check for related items:
   - Other debt in same component
   - Dependencies on this resolution
   
3. If solution exists in VideoCommentator:
   ```bash
   ./dev-cli ask "VideoCommentator [component] implementation"
   ```
   - Check if we can reuse existing code

### Resolution Process

1. Implement the fix following patterns:
   - Use knowledge base guidance
   - Follow PRD specifications
   - Apply VideoCommentator patterns
   
2. Remove TODO/FIXME comments:
   - Search for debt ID in codebase
   - Remove or update comments
   - Ensure no orphaned references

3. Test thoroughly:
   - Unit tests for the fix
   - Integration tests if applicable
   - Verify no regressions
   - Check performance impact

4. Update technical debt tracking:
   - Edit `scripts/update_technical_debt.py`
   - Add to resolved_items list
   - Include resolution notes

5. If pattern discovered:
   - Add to knowledge base
   - Document for future reference

6. Generate report showing:
   - What was fixed
   - Any new debt discovered
   - Impact on system
   - Remaining related debt

## Update Script Template

Edit `scripts/update_technical_debt.py`:

```python
# For fully resolved items
resolved_items = [
    {
        "component": "api/endpoints",
        "item_id": "API-002",
        "resolution": "Implemented Celery task integration using existing patterns from workers module. Added progress tracking and error handling."
    }
]

# For partially resolved (IN_PROGRESS)
tech_debt.update_debt_status(
    "core/monitoring",
    "MON-001",
    DebtStatus.IN_PROGRESS,
    "Implemented logging and memory monitoring. Still need metrics collection and health checks."
)

# For deferred items
tech_debt.update_debt_status(
    "providers/optimization",
    "PERF-001",
    DebtStatus.DEFERRED,
    "Deferred until after v1.0 release. Current performance is acceptable for MVP."
)
```

## Verification Steps

1. Confirm fix works:
   ```bash
   # Run specific tests
   pytest tests/test_[component].py -v
   
   # Check no TODOs remain
   grep -r "API-002" services/
   ```

2. Update documentation if needed:
   - API docs for endpoint changes
   - Configuration docs for new settings
   - README for new dependencies

3. Check for regressions:
   ```bash
   # Run full test suite
   pytest services/backend/tests/
   ```

## Example: Resolving API-002

```bash
# 1. Implement the fix in code
# 2. Remove TODO comments
# 3. Run tests

# 4. Update the tracking
vim scripts/update_technical_debt.py
# Add:
# resolved_items = [
#     {
#         "component": "api/endpoints",
#         "item_id": "API-002",
#         "resolution": "Connected all API endpoints to Celery tasks..."
#     }
# ]

# 5. Run update
python scripts/update_technical_debt.py

# 6. Verify resolution
./dev-cli prompt debt-check | grep "API-002"
```

## Resolution Statuses

- **RESOLVED**: Completely fixed, tested, and deployed
- **IN_PROGRESS**: Partially fixed, more work needed
- **DEFERRED**: Postponed with valid reason
- **WON_T_FIX**: Decided not to fix (document why)

## Example Usage
```bash
# Resolve a debt item
./dev-cli prompt debt-resolve API-002

# Check resolution
./dev-cli prompt debt-check

# Update project status
./dev-cli prompt status-update
```

## Related Prompts
- `debt-check` - Verify debt was resolved
- `status-update` - Update project progress
- `knowledge-add` - Document solution pattern