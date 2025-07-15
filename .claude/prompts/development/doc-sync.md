# Documentation Sync Template

## Description
Update all documentation after implementing or modifying components to ensure consistency across the project.

## When to Use
- After completing a feature or component
- When making architectural changes
- After fixing significant bugs
- Before releases or milestones
- When onboarding new team members

## Prerequisites
- Implementation completed and tested
- Clear understanding of changes made
- Access to all documentation locations

## Documentation Locations

1. **Code Documentation**
   - Docstrings in Python files
   - Inline comments for complex logic
   - Type hints and annotations

2. **API Documentation**
   - OpenAPI/Swagger specs
   - Endpoint descriptions
   - Request/response examples

3. **Technical Documentation**
   - `/docs/` directory
   - Architecture decisions
   - Service documentation

4. **Project Management**
   - PRD progress tracking
   - MongoDB status updates
   - Technical debt items

5. **Knowledge Base**
   - Patterns and solutions
   - Lessons learned
   - Implementation guides

6. **Configuration**
   - `.env.example`
   - `README.md` files
   - Deployment guides

## Steps

### 1. Update PRD Progress

Check and update `/docs/new/video-intelligence-prd.md`:

- Mark completed items in implementation phases
- Update component status
- Note any deviations from original spec
- Add references to implementation files

Example:
```markdown
### 4.2 Video Chunking ✅
- Status: Completed
- Implementation: `/services/backend/services/chunking/`
- Tests: `/services/backend/tests/test_chunking/`
- Notes: Added configurable overlap for better scene continuity
```

### 2. Update Technical Documentation

#### API Documentation
If new endpoints added:
```python
@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Start video analysis",
    description="""
    Initiates video analysis with the specified configuration.
    
    The analysis runs asynchronously and returns a job ID for tracking.
    Use the job status endpoint to monitor progress.
    """,
    responses={
        202: {"description": "Analysis started successfully"},
        400: {"description": "Invalid request parameters"},
        404: {"description": "Video not found"}
    }
)
```

#### Service Documentation
Create/update service README:
```markdown
# [Service Name]

## Overview
Brief description of what this service does.

## Architecture
How it fits into the overall system.

## Configuration
- `ENV_VAR_1`: Description (default: value)
- `ENV_VAR_2`: Description (required)

## Usage
```python
from services.xxx import ServiceName

service = ServiceName()
result = await service.process(data)
```

## API Reference
Document public methods and their parameters.

## Error Handling
Common errors and how to handle them.
```

### 3. Update MongoDB Schema Documentation

For new or modified models:
```python
class Video(Document):
    """
    Video document representing a video file in the system.
    
    Attributes:
        title: Human-readable video title
        s3_uri: S3 location of the source video
        status: Current processing status
        duration: Video duration in seconds
        metadata: Additional video metadata (resolution, codec, etc.)
        
    Relationships:
        scenes: List of Scene documents via scene_ids
        processing_jobs: Related ProcessingJob documents
    """
```

### 4. Update Knowledge Base

Add significant patterns or solutions:

```bash
# Create knowledge document
cat > dev-knowledge-base/docs/new/[topic]-[date].md << 'EOF'
# [Pattern/Solution Title]

## Context
When implementing [component], discovered [pattern].

## Implementation
```python
# Code example
```

## Benefits
- Benefit 1
- Benefit 2

## Trade-offs
- Trade-off 1

## References
- Implemented in: [file]
- Related to: [component]
EOF

# Run ingestion
cd dev-knowledge-base
python ingestion/extract_knowledge.py
```

### 5. Sync AI Assistant Files

#### Update CLAUDE.md
If new patterns or important paths:
```markdown
## Critical Patterns from Video Intelligence

### X. New Pattern Name
```python
# Pattern example
```
Reference: `services/backend/[path]`
```

#### Update Prompt Templates
If new workflows discovered, add to `.claude/prompts/workflows/`

### 6. Update Configuration Documentation

#### Environment Variables
Update `.env.example`:
```bash
# Video Processing
VIDEO_CHUNK_DURATION=30  # Chunk duration in seconds
VIDEO_CHUNK_OVERLAP=5    # Overlap between chunks

# New Provider
NEW_PROVIDER_API_KEY=    # Required for NewProvider integration
NEW_PROVIDER_ENDPOINT=   # Optional, defaults to https://api.provider.com
```

#### Update main README.md
- New features in feature list
- Updated setup instructions if needed
- New dependencies

### 7. Verification Checklist

Run through verification:

```bash
# Check all file paths are correct
find . -name "*.md" -exec grep -l "/path/to/check" {} \;

# Verify code examples work
python -m doctest path/to/file.py

# Check for broken links
# (use a link checker tool)

# Ensure schemas match implementation
# Compare models.py with documentation
```

## Common Documentation Updates

### After Adding a Feature
1. PRD: Mark feature as completed
2. API docs: Document new endpoints
3. README: Add to feature list
4. Knowledge base: Document patterns used
5. Tests: Document test coverage

### After Fixing a Bug
1. Knowledge base: Document root cause and fix
2. Code: Add comments explaining fix
3. Tests: Document regression test
4. Technical debt: Update if partial fix

### After Refactoring
1. Update all file path references
2. Update architecture diagrams
3. Update import examples
4. Document why refactoring was done

### After Performance Optimization
1. Document benchmarks before/after
2. Explain optimization technique
3. Add to knowledge base
4. Note any trade-offs

## Documentation Templates

### API Endpoint Documentation
```python
"""
Endpoint: POST /api/v1/[resource]
Description: [What it does]

Request Body:
{
    "field1": "string",
    "field2": 123
}

Response (200):
{
    "id": "string",
    "status": "success"
}

Errors:
- 400: Invalid input
- 404: Resource not found
- 500: Internal error
"""
```

### Service Method Documentation
```python
def process_data(self, input_data: Dict[str, Any]) -> ProcessResult:
    """
    Process input data according to business rules.
    
    This method performs validation, transformation, and persistence
    of the input data. It handles errors gracefully and provides
    detailed feedback on processing results.
    
    Args:
        input_data: Dictionary containing:
            - field1 (str): Description of field1
            - field2 (int): Description of field2
            - field3 (optional, str): Description of field3
    
    Returns:
        ProcessResult object containing:
            - success (bool): Whether processing succeeded
            - data (Any): Processed data if successful
            - errors (List[str]): Any errors encountered
    
    Raises:
        ValidationError: If input data is invalid
        ProcessingError: If processing fails
        
    Example:
        >>> service = ProcessingService()
        >>> result = service.process_data({"field1": "value"})
        >>> print(result.success)
        True
    """
```

## Automation

Consider automating documentation updates:

1. **API Docs**: Use FastAPI's automatic OpenAPI generation
2. **Code Docs**: Use tools like Sphinx for Python
3. **Diagrams**: Use code-to-diagram tools
4. **Link Checking**: CI/CD pipeline integration

## Final Checklist

- [ ] PRD progress updated
- [ ] API documentation current
- [ ] Service READMEs updated
- [ ] MongoDB schemas documented
- [ ] Knowledge base entries added
- [ ] Configuration documented
- [ ] AI assistant files synced
- [ ] Main README updated
- [ ] All code examples tested
- [ ] File paths verified
- [ ] Links checked

## Related Prompts
- `knowledge-add` - Add to knowledge base
- `status-update` - Update project status
- `test` - Ensure test documentation
- `feature` - Feature documentation