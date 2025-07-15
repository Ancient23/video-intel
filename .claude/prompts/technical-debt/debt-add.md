# Add Technical Debt Item

## Description
Add a new technical debt item for an issue or incomplete implementation discovered during development.

## When to Use
- When implementing a temporary solution
- When discovering missing functionality
- When finding security vulnerabilities
- When skipping proper implementation due to time
- When noticing performance issues

## Prerequisites
- Identified the issue clearly
- Know the file location
- Can estimate the effort to fix
- Understand the impact

## Input Required
- **Issue**: Brief description of the problem
- **Location**: File path and line numbers (if applicable)
- **Severity**: critical/high/medium/low
- **Category**: security/performance/incomplete/hardcoded/missing_integration/testing/documentation/error_handling/configuration/monitoring
- **Effort**: Estimated hours to fix
- **Impact**: How this affects the system

## Steps

1. Create the debt item structure:
   ```python
   from backend.models import TechnicalDebt, TechnicalDebtItem, DebtSeverity, DebtCategory
   
   item = TechnicalDebtItem(
       id="[CATEGORY-NNN]",  # e.g., API-003, SEC-002
       title="[Short descriptive title]",
       description="[Detailed description including impact and suggested fix]",
       file_path="[path/to/file.py]",
       line_numbers=[line1, line2],  # Optional
       category=DebtCategory.[CATEGORY],
       severity=DebtSeverity.[SEVERITY],
       estimated_effort_hours=[float],
       tags=["tag1", "tag2", "relevant-tags"]
   )
   ```

2. Add to technical debt document:
   - Edit `scripts/init_technical_debt.py`
   - Add to the `debt_items` list
   - Specify the component/service area

3. If discovered during implementation:
   - Add TODO/FIXME comment in code
   - Reference the debt item ID
   ```python
   # TODO: [DEBT-ID] - Brief description
   # See technical debt tracking for full details
   ```

4. Update project status if this blocks features:
   - Note in blocked_tasks if applicable
   - Add to project notes

5. Report the debt item details and impact

## ID Naming Convention
- **SEC-XXX**: Security issues
- **API-XXX**: API-related debt
- **PROV-XXX**: Provider issues
- **CORE-XXX**: Core service debt
- **DB-XXX**: Database issues
- **TEST-XXX**: Testing debt
- **DOC-XXX**: Documentation debt
- **CONFIG-XXX**: Configuration issues
- **MON-XXX**: Monitoring debt
- **PERF-XXX**: Performance issues

## Example: Adding API Rate Limiting Debt

```python
# In scripts/init_technical_debt.py, add to debt_items:
{
    "component": "api/security",
    "item": TechnicalDebtItem(
        id="SEC-002",
        title="Missing API Rate Limiting",
        description="API endpoints have no rate limiting, making them vulnerable to abuse. Need to implement rate limiting using Redis and slowapi.",
        file_path="services/backend/api/v1/routers/video_analysis.py",
        line_numbers=[120, 150, 200],  # Line numbers of affected endpoints
        category=DebtCategory.SECURITY,
        severity=DebtSeverity.HIGH,
        estimated_effort_hours=8.0,
        tags=["api", "security", "rate-limiting", "redis"]
    )
}
```

Then run:
```bash
python scripts/init_technical_debt.py
```

## In-Code Documentation
```python
# In the affected file:
@router.post("/analyze")
async def analyze_video(request: VideoAnalysisRequest):
    # TODO: [SEC-002] Implement rate limiting
    # This endpoint is vulnerable to abuse without rate limits
    # See technical debt tracking for implementation plan
    
    # ... rest of the implementation
```

## Example Usage
```bash
# Add new debt item (edit script first)
vim scripts/init_technical_debt.py
python scripts/init_technical_debt.py

# Quick add with template
./dev-cli prompt debt-add --template

# Verify it was added
./dev-cli prompt debt-check | grep "SEC-002"
```

## Related Prompts
- `debt-check` - View current debt before adding
- `debt-resolve` - Mark debt as resolved
- `status-update` - Update project status if blocked