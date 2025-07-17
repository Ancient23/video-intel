# Bug Investigation and Fix

## Description
Debug and fix issues in the Video Intelligence Platform using systematic investigation.

## When to Use
- Application not working as expected
- Errors in logs or console
- Test failures
- Performance problems
- Integration issues

## Prerequisites
- Bug symptoms documented
- Access to logs and monitoring
- Test environment available
- Ability to reproduce issue

## Input Required
- **Component**: Where the bug occurs
- **Symptoms**: What's happening wrong
- **Expected**: What should happen
- **Steps**: How to reproduce

## Investigation Process

1. **MANDATORY** Search Graph-RAG for similar issues:
   ```bash
   # Search for error patterns
   ./dev-cli search "[error message]"
   ./dev-cli search "[component] common issues"
   ./dev-cli search "[component] debugging"
   
   # Explore related components
   ./dev-cli explore "[component]" --depth 2
   
   # Ask for solutions
   ./dev-cli ask "How to fix [error type]"
   ./dev-cli ask "Best practices for debugging [component]"
   ```

2. Review relevant logs:
   ```bash
   # Docker compose logs
   docker compose logs -f [service]
   
   # MongoDB query logs
   docker compose exec mongodb mongosh video_intelligence
   db.setLogLevel(1)
   
   # Celery worker logs
   docker compose logs -f celery_worker
   
   # Application logs
   tail -f logs/app.log
   ```

3. Check MongoDB data:
   ```python
   # Check processing job status
   from backend.models import ProcessingJob
   job = await ProcessingJob.find_one({"_id": job_id})
   print(job.error_message)
   
   # Check component states
   from backend.models import Video
   video = await Video.find_one({"_id": video_id})
   print(video.status, video.error_details)
   ```

4. Identify root cause:
   - Compare with PRD specifications
   - Check against VideoCommentator patterns
   - Verify environment setup
   - Check for missing dependencies
   - Review recent changes

5. Fix approach:
   - Minimal change for immediate fix
   - Proper solution if different
   - Add to knowledge base
   - Update tests to prevent regression

6. Test the fix:
   - Reproduce original issue first
   - Apply fix
   - Verify fix works
   - Check for regressions
   - Run related tests

7. Update tracking:
   - Add to knowledge base if significant
   - Update technical debt if partial fix
   - Document in code comments
   - Update project status

## Common Issues and Solutions

### MongoDB Connection Issues
```python
# Symptom: Connection refused
# Check: MongoDB running
docker compose ps mongodb

# Fix: Restart MongoDB
docker compose restart mongodb

# Verify connection
from backend.core.database import Database
await Database.connect()
```

### Celery Task Not Running
```python
# Symptom: Tasks stay pending
# Check: Worker running
celery -A celery_app inspect active

# Check: Task registered
celery -A celery_app inspect registered

# Fix: Restart worker
docker compose restart celery_worker
```

### S3 Access Errors
```python
# Symptom: Access denied
# Check: Credentials
echo $AWS_ACCESS_KEY_ID

# Fix: Update .env and restart
source .env
docker compose restart api
```

### Provider API Failures
```python
# Symptom: Provider errors
# Check: API keys valid
# Check: Rate limits
# Check: Service status

# Fix: Implement retry logic
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def call_provider():
    # Provider call
```

## Debugging Tools

### Structured Logging
```python
import structlog
logger = structlog.get_logger()

# Add context to track issues
logger.info("Processing video",
    video_id=video_id,
    provider=provider_name,
    chunk_count=len(chunks),
    user_id=user_id
)
```

### Interactive Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with ipdb (better interface)
import ipdb; ipdb.set_trace()

# Async debugging
import aiodebug; aiodebug.set_trace()
```

### MongoDB Query Debugging
```python
# Enable query logging
from mongoengine import QuerySet
QuerySet._debug = True

# Check slow queries
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().limit(5).sort({ ts: -1 })
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function to profile
```

## Fix Verification

1. Unit test for the fix:
```python
def test_bug_fix():
    # Arrange - set up bug conditions
    
    # Act - run fixed code
    
    # Assert - verify fix works
```

2. Integration test:
```python
async def test_integration_fix():
    # Test with real MongoDB
    # Test with real Redis
    # Verify end-to-end
```

3. Regression test:
```python
def test_no_regression():
    # Test related functionality
    # Ensure nothing broken
```

## Documentation

After fixing, document:

1. **In Code**:
```python
# BUG FIX: [Issue description]
# Root cause: [What caused it]
# Solution: [How it was fixed]
# Date: [When fixed]
# Ticket: [Reference if any]
```

2. **In Knowledge Base**:
Create `dev-knowledge-base/docs/bugs/[component]-[issue].md`:
```markdown
# [Component] - [Issue Title]

## Symptom
What was observed

## Root Cause
Why it happened

## Solution
How it was fixed

## Prevention
How to avoid in future

## Related
- Similar issues
- Relevant docs
```

## Example Usage
```bash
# Investigate video processing failure
./dev-cli prompt bug --component "video_chunking" --symptom "FFmpeg timeout"

# Debug API 500 errors
./dev-cli prompt bug --component "api" --symptom "Internal server error on /analyze"
```

## Related Prompts
- `debt-add` - If partial fix, add technical debt
- `test` - Add tests to prevent regression
- `knowledge-add` - Document the solution
- `status-update` - Update project status