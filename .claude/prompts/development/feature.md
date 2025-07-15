# New Feature Implementation

## Description
Implement a new feature for the Video Intelligence Platform following established patterns.

## When to Use
- Adding new functionality
- Implementing a PRD requirement
- Creating a new service or component
- Extending existing features

## Prerequisites
- Feature requirements clear
- Related PRD section identified
- Dependencies available
- Development environment ready

## Input Required
- **Feature**: Description of the feature
- **Phase**: Which PRD phase this belongs to
- **Components**: Which services/components affected

## Steps

1. Knowledge base check:
   ```bash
   ./dev-cli ask "[feature] implementation patterns"
   ./dev-cli ask "Similar features in VideoCommentator"
   ```

2. Review PRD requirements:
   - Check feature specifications
   - MongoDB schema requirements
   - Provider integrations needed
   - API endpoints required

3. Design approach:
   - Which services affected
   - New models/schemas needed
   - Celery tasks required
   - API endpoints
   - Caching strategy

4. Implementation checklist:
   - [ ] Follow PRD structure
   - [ ] Use knowledge base patterns
   - [ ] Create services in correct directories
   - [ ] Add proper error handling
   - [ ] Include cost tracking (if applicable)
   - [ ] Add comprehensive logging
   - [ ] Write type hints
   - [ ] Add docstrings

5. Testing requirements:
   - Unit tests for service logic
   - Integration test with MongoDB
   - Local Docker testing
   - Error scenario testing

6. Update tracking:
   - MongoDB project status
   - Knowledge base with patterns
   - Technical debt if any
   - PRD progress tracking

## Feature Structure

### Service Implementation
```python
# services/backend/services/[feature]/[feature]_service.py
import structlog
from typing import List, Optional
from ...models import [RelatedModel]
from ...schemas import [FeatureSchema]

logger = structlog.get_logger()

class [Feature]Service:
    """Service for handling [feature description]"""
    
    async def create_[feature](
        self, 
        data: [FeatureSchema]
    ) -> [RelatedModel]:
        """Create new [feature] with validation"""
        logger.info("Creating [feature]", data=data.model_dump())
        
        # Validate
        await self._validate_data(data)
        
        # Create in MongoDB
        model = [RelatedModel](**data.model_dump())
        await model.create()
        
        # Post-processing if needed
        await self._post_process(model)
        
        return model
```

### API Endpoint
```python
# services/backend/api/v1/routers/[feature].py
from fastapi import APIRouter, Depends, HTTPException
from ....schemas.api import [Feature]Request, [Feature]Response
from ....services.[feature] import [Feature]Service

router = APIRouter(prefix="/[feature]", tags=["[feature]"])

@router.post("/", response_model=[Feature]Response)
async def create_[feature](
    request: [Feature]Request,
    service: [Feature]Service = Depends()
):
    """Create new [feature]"""
    try:
        result = await service.create_[feature](request)
        return [Feature]Response.from_model(result)
    except ValueError as e:
        raise HTTPException(400, str(e))
```

### Celery Task (if async)
```python
# services/backend/workers/[feature]_tasks.py
from celery import celery_app
from ..services.[feature] import [Feature]Service

@celery_app.task(bind=True)
def process_[feature]_async(self, feature_id: str):
    """Process [feature] asynchronously"""
    try:
        service = [Feature]Service()
        result = service.process(feature_id)
        return {"status": "completed", "result": result}
    except Exception as e:
        self.retry(exc=e, countdown=60)
```

## Common Patterns

### Error Handling
```python
try:
    # Main logic
    result = await process()
except ValidationError as e:
    logger.warning("Validation failed", error=str(e))
    raise HTTPException(400, e.errors())
except NotFoundException as e:
    logger.warning("Not found", error=str(e))
    raise HTTPException(404, str(e))
except Exception as e:
    logger.error("Unexpected error", error=str(e))
    raise HTTPException(500, "Internal server error")
```

### Caching
```python
from utils import cache_api_call

@cache_api_call(service='[feature]', ttl_hours=24)
async def get_expensive_data(params):
    # Expensive operation
    return result
```

### Progress Tracking
```python
async def long_running_task(job_id: str):
    job = await ProcessingJob.get(job_id)
    
    # Update progress
    await job.update_progress(0.25, "Starting processing")
    # ... work ...
    await job.update_progress(0.75, "Almost done")
    # ... finish ...
    await job.mark_completed(result)
```

## Example Usage
```bash
# Implement embeddings service
./dev-cli prompt feature --name "embeddings" --phase "EMBEDDINGS"

# Add new API endpoint
./dev-cli prompt feature --name "video_search" --component "api"
```

## Testing Template
```python
# services/backend/tests/test_[feature].py
import pytest
from ..services.[feature] import [Feature]Service

class Test[Feature]Service:
    @pytest.fixture
    def service(self):
        return [Feature]Service()
    
    async def test_create_[feature](self, service):
        # Arrange
        data = {"field": "value"}
        
        # Act
        result = await service.create_[feature](data)
        
        # Assert
        assert result.field == "value"
        assert result.id is not None
```

## Related Prompts
- `impl-plan` - Detailed implementation planning
- `feature-provider` - Provider integration
- `test` - Add test coverage
- `status-update` - Update project status