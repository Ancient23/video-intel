# Technical Debt Status Check

## Description
Show the current technical debt status with priority items and analysis.

## When to Use
- Before starting new feature work
- During sprint planning
- When experiencing blockers
- For weekly debt reviews
- Before releases

## Prerequisites
- MongoDB running
- Technical debt collection initialized
- Virtual environment activated

## Steps

1. Query technical debt collection:
   ```bash
   python scripts/init_technical_debt.py
   ```

2. Analyze the report showing:
   - Total debt items and open items
   - Critical and high priority items
   - Estimated effort hours remaining
   - Items by category and severity
   - Recently updated items

3. For critical/high priority items:
   - Show file locations and line numbers
   - Explain impact on system
   - Suggest resolution approach
   - Estimate effort required

4. Check if any debt blocks current tasks:
   - Cross-reference with project status
   - Identify dependencies
   - Find quick wins

5. Generate recommendations:
   - Which debt to address first
   - Quick wins (< 2 hours)
   - Items that unblock features
   - Security critical items

## Report Analysis

### Severity Priorities
1. **CRITICAL** - Fix immediately (security, data loss)
2. **HIGH** - Fix before next phase (blockers)
3. **MEDIUM** - Fix before production (quality)
4. **LOW** - Fix during refactoring (cleanup)

### Quick Win Identification
Look for:
- LOW severity with < 2 hour estimates
- Simple configuration fixes
- Missing error handling
- Documentation updates

## Example Output
```
=== Technical Debt Report ===
Total Items: 19 (16 open, 2 resolved, 1 in progress)
Estimated Hours: 198

Critical Items (1):
  [SEC-001] Placeholder Authentication - 16h
  Location: services/backend/core/deps.py:26-34
  Impact: No real authentication, security vulnerability
  Fix: Implement JWT validation with proper user management

High Priority Items (10):
  [PROV-001] NVIDIA VILA S3 Download - 4h
  Location: services/backend/services/analysis/providers/nvidia_vila.py:80-81
  Impact: Provider cannot process S3 videos
  Fix: Implement using existing s3_utils.download_from_s3()

Quick Wins:
  [HARD-001] Hardcoded Retry Limits - 1h
  [HARD-002] Hardcoded Model Temperature - 1h

Blocking Current Work:
  [API-002] blocks video processing pipeline
  [TASK-001] blocks job progress tracking
```

## Filtering Options

```bash
# Show only critical/high items
python scripts/init_technical_debt.py | grep -A10 "CRITICAL\|HIGH"

# Show by category
python scripts/init_technical_debt.py | grep -A5 "security"

# Show quick wins
python scripts/init_technical_debt.py | grep -B2 "1.0h\|2.0h"
```

## Example Usage
```bash
# Full debt check
./dev-cli prompt debt-check

# Check specific component
python scripts/init_technical_debt.py | grep -A10 "api/"

# Export for planning
./dev-cli prompt debt-check > debt_report_$(date +%Y%m%d).txt
```

## Related Prompts
- `debt-add` - Add newly discovered debt
- `debt-resolve` - Mark debt as resolved
- `status-check` - View alongside project status