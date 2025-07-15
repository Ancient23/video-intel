# Implementation Plan Step Execution

## Description
Create and execute a detailed implementation plan for a component or feature from the Video Intelligence PRD.

## When to Use
- Starting a new component implementation
- Implementing a complex feature
- Need structured approach to development
- Want to ensure PRD compliance

## Prerequisites
- Clear understanding of the component/feature
- PRD section identified
- Development environment set up
- Knowledge base accessible

## Input Required
- **Component**: Specific component from PRD
- **PRD Section**: Section reference in the PRD
- **Scope**: What exactly needs to be implemented

## Steps

### Pre-Execution Phase

1. Query knowledge base for patterns:
   ```bash
   ./dev-cli ask "How to implement [component]"
   ./dev-cli ask "VideoCommentator [similar feature]"
   ```

2. Check MongoDB schemas:
   - Review relevant models in `services/backend/models/`
   - Ensure schema alignment with PRD
   - Check for existing related models

3. Review old VideoCommentator code:
   - Check path references in CLAUDE.md
   - Look for similar implementations
   - Note reusable patterns

4. Present implementation plan:
   - Components to create/modify
   - Patterns to follow
   - Potential issues
   - Dependencies
   - **WAIT for approval before proceeding**

### Implementation Phase

1. Create service structure following PRD layout:
   ```
   services/backend/services/[component]/
   ├── __init__.py
   ├── [main_service].py
   ├── schemas.py
   └── utils.py
   ```

2. Use patterns from knowledge base:
   - Provider abstraction if applicable
   - Caching strategies
   - Error handling patterns
   - Async/await for I/O

3. Implement with best practices:
   - Proper error handling (try/except blocks)
   - Cost tracking (if provider integration)
   - Progress updates to MongoDB
   - Celery task patterns (if async)
   - Comprehensive logging
   - Type hints and docstrings

4. Test implementation locally:
   - Create test script in `tests/`
   - Verify MongoDB updates work
   - Check logs for errors
   - Test error scenarios

### Post-Implementation Phase

1. Update project status in MongoDB:
   ```bash
   python scripts/update_project_status.py
   ```

2. Document any new patterns discovered:
   - Add to `dev-knowledge-base/docs/`
   - Include code examples
   - Note any gotchas

3. Add to knowledge base if significant:
   ```bash
   cd dev-knowledge-base
   python ingestion/extract_knowledge.py
   ```

4. Generate report showing:
   - What was completed
   - Any issues found
   - Technical debt created
   - Next logical step

## Implementation Template

```python
"""
[Component Name] Service
Implements [PRD section reference]
"""
import structlog
from typing import Optional, List
from ..base import BaseService  # If applicable

logger = structlog.get_logger()

class [ComponentName]Service(BaseService):
    """
    Service for [component purpose]
    
    This implements the [component] as specified in PRD section [X.Y]
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize service with configuration"""
        super().__init__(config)
        logger.info("Initialized [component] service")
    
    async def process(self, input_data: dict) -> dict:
        """
        Main processing method
        
        Args:
            input_data: Input parameters
            
        Returns:
            Processing results
            
        Raises:
            ServiceError: If processing fails
        """
        try:
            # Implementation
            logger.info("Processing", data=input_data)
            
            # Update progress if applicable
            await self._update_progress(0.5, "Processing halfway")
            
            # Return results
            return {"status": "success", "data": result}
            
        except Exception as e:
            logger.error("Processing failed", error=str(e))
            raise ServiceError(f"Failed to process: {e}")
```

## Example Usage

```bash
# Plan implementation for knowledge graph
./dev-cli prompt impl-plan --component "knowledge_graph" --prd "Section 4.3"

# Plan provider integration
./dev-cli prompt impl-plan --component "openai_provider" --prd "Section 3.2"
```

## Checklist

- [ ] Knowledge base queried for patterns
- [ ] VideoCommentator code reviewed
- [ ] MongoDB schemas checked
- [ ] Implementation plan presented
- [ ] Service structure created
- [ ] Core functionality implemented
- [ ] Error handling added
- [ ] Tests written
- [ ] Logging comprehensive
- [ ] Project status updated
- [ ] Technical debt documented
- [ ] Knowledge base updated

## Related Prompts
- `feature` - Simpler feature implementation
- `feature-provider` - Provider-specific implementation
- `test` - Add test coverage
- `status-update` - Update project status