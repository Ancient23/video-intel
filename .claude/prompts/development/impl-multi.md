# Multi-Component Implementation Session

## Description
Implement multiple related components from the PRD in a coordinated sequence.

## When to Use
- Implementing a complete feature that spans multiple services
- Building interdependent components
- Creating a full vertical slice of functionality
- Implementing an entire PRD phase

## Prerequisites
- Clear understanding of all components
- Dependencies mapped out
- PRD sections identified
- Development environment ready

## Input Required
- **Components**: List of components to implement
- **Dependencies**: Order and relationships
- **PRD References**: Relevant sections

## Session Planning

### 1. Dependency Analysis
```bash
# Query for implementation order
./dev-cli ask "Implementation order for [components]"
./dev-cli ask "Dependencies between [component1] and [component2]"
```

### 2. Component Mapping
Create a dependency graph:
```
Component A (data models)
    ↓
Component B (services)
    ↓
Component C (API endpoints)
    ↓
Component D (workers/tasks)
```

### 3. Knowledge Base Research
For each component:
```bash
./dev-cli ask "How to implement [component]"
./dev-cli ask "Integration patterns for [components]"
```

### 4. MongoDB Schema Review
- Check relationships between models
- Ensure consistent field naming
- Verify index requirements
- Plan for data migrations

## Implementation Order

### Phase 1: Foundation Components
1. **Data Models** (if needed)
   - Create/update MongoDB models
   - Define relationships
   - Add indexes

2. **Core Services**
   - Business logic implementation
   - Interface definitions
   - Error handling

3. **Utilities/Helpers**
   - Shared functionality
   - Common patterns
   - Reusable components

### Phase 2: Integration Components
4. **Service Integration**
   - Connect services
   - Data flow implementation
   - Transaction handling

5. **API Layer**
   - Create endpoints
   - Request/response schemas
   - Authentication/authorization

6. **Background Tasks**
   - Celery task definitions
   - Task orchestration
   - Progress tracking

### Phase 3: Testing & Documentation
7. **Integration Tests**
   - End-to-end workflows
   - Component interaction tests
   - Error scenarios

8. **Documentation**
   - API documentation
   - Service documentation
   - Usage examples

## Implementation Workflow

### For Each Component:

1. **Pre-Implementation**
   ```bash
   # Check patterns
   ./dev-cli ask "Best practices for [component]"
   
   # Review similar code
   grep -r "similar_pattern" /path/to/VideoCommentator
   ```

2. **Implementation**
   - Follow single component template
   - Maintain consistent patterns
   - Use shared utilities
   - Add comprehensive logging

3. **Testing**
   - Unit tests for the component
   - Integration tests with previous components
   - Verify data flow

4. **Status Update**
   ```python
   # Update after each component
   python scripts/update_project_status.py
   ```

## Integration Points

### Service-to-Service
```python
# Consistent service interfaces
class ServiceA:
    async def get_data(self, id: str) -> Model:
        pass

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a
    
    async def process(self, id: str):
        data = await self.service_a.get_data(id)
        # Process data
```

### API-to-Service
```python
# Dependency injection pattern
@router.post("/process")
async def process_endpoint(
    request: ProcessRequest,
    service: ServiceB = Depends(get_service_b)
):
    result = await service.process(request.id)
    return ProcessResponse(result=result)
```

### Service-to-Worker
```python
# Async task triggering
from workers.tasks import process_async

class ServiceC:
    def trigger_processing(self, data_id: str):
        task = process_async.delay(data_id)
        return task.id
```

## Example: Video Processing Pipeline

### Components to Implement:
1. Video ingestion service
2. Chunking service  
3. Analysis orchestrator
4. Result aggregator
5. API endpoints
6. Background workers

### Implementation Sequence:

#### 1. Video Model Updates
```python
# models/video.py
class Video(Document):
    # Core fields
    processing_status: ProcessingStatus
    chunks: List[ChunkReference]
    analysis_results: List[AnalysisResult]
```

#### 2. Ingestion Service
```python
# services/ingestion/video_ingestion.py
class VideoIngestionService:
    async def ingest(self, video_url: str) -> Video:
        # Download, validate, create record
```

#### 3. Chunking Service
```python
# services/chunking/video_chunker.py
class VideoChunkingService:
    async def chunk_video(self, video: Video) -> List[Chunk]:
        # Create chunks with overlap
```

#### 4. Continue with remaining components...

## Progress Tracking

### After Each Component:
1. Run component tests
2. Verify integration with previous components
3. Update project status
4. Document any issues or patterns
5. Check for technical debt

### Daily Summary:
```bash
# End of day status check
./dev-cli prompt status-check

# Document progress
./dev-cli prompt status-update
```

## Integration Testing

### Test Full Workflow:
```python
@pytest.mark.integration
async def test_full_pipeline():
    # 1. Ingest video
    video = await ingestion_service.ingest(test_url)
    
    # 2. Chunk video
    chunks = await chunking_service.chunk_video(video)
    
    # 3. Analyze chunks
    results = await orchestrator.analyze(chunks)
    
    # 4. Aggregate results
    final_result = await aggregator.aggregate(results)
    
    # Verify complete flow
    assert final_result.status == "completed"
```

## Common Pitfalls

1. **Circular Dependencies**
   - Use dependency injection
   - Define clear interfaces
   - Avoid tight coupling

2. **Inconsistent Data Models**
   - Maintain naming conventions
   - Use shared schemas
   - Document relationships

3. **Missing Error Handling**
   - Handle failures at each level
   - Implement retry logic
   - Log comprehensively

4. **Performance Issues**
   - Profile after each component
   - Add caching where needed
   - Optimize database queries

## Documentation

### Component Documentation Template:
```markdown
# [Component Group] Implementation

## Components Implemented
1. Component A - Description
2. Component B - Description

## Architecture
[Diagram or description of how components interact]

## API Changes
- New endpoints added
- Modified endpoints

## Database Changes
- New collections/fields
- Index changes

## Configuration
- New environment variables
- Updated settings

## Usage Examples
[Code examples showing how to use the components]
```

## Completion Checklist

- [ ] All components implemented
- [ ] Unit tests for each component
- [ ] Integration tests for workflows
- [ ] API documentation updated
- [ ] MongoDB schemas documented
- [ ] Error handling comprehensive
- [ ] Performance acceptable
- [ ] Technical debt documented
- [ ] Knowledge base updated
- [ ] Project status current

## Related Prompts
- `impl-plan` - Single component planning
- `feature` - Individual feature implementation
- `test` - Testing strategies
- `status-update` - Progress tracking