# Add Knowledge to Development Database

## Description
Add new patterns, solutions, or learnings to the development knowledge base for future reference.

## When to Use
- After solving a complex problem
- When discovering a useful pattern
- After implementing a new feature
- When finding a better approach
- After debugging difficult issues
- When learning from mistakes

## Prerequisites
- Knowledge worth documenting
- Clear understanding of the pattern/solution
- Markdown formatting knowledge
- Access to dev-knowledge-base directory

## Input Required
- **Knowledge Type**: Pattern/Lesson/Issue/Solution/Best Practice
- **Component**: Which component/service this relates to
- **Context**: When this knowledge applies
- **Details**: The actual knowledge to document

## Steps

1. Create knowledge document:
   ```bash
   # Navigate to knowledge base
   cd dev-knowledge-base/docs/new/
   
   # Create new document
   cat > [topic]-[date].md << 'EOF'
   # [Title]
   
   ## Context
   [When/where this applies]
   
   ## Problem
   [What issue this solves - optional]
   
   ## Pattern/Solution
   [The actual pattern or solution]
   
   ## Example
   ```python
   # Code example showing the pattern
   ```
   
   ## Benefits
   - [Why this approach is good]
   - [What it improves]
   
   ## Considerations
   - [When not to use this]
   - [Potential drawbacks]
   
   ## References
   - Related to: [component/file]
   - VideoCommentator equivalent: [if applicable]
   - External docs: [links]
   EOF
   ```

2. Run ingestion to index the new knowledge:
   ```bash
   cd dev-knowledge-base
   python ingestion/extract_knowledge.py
   ```

3. Verify it's searchable:
   ```bash
   ./dev-cli ask "[keyword from your addition]"
   ```

4. Update project notes in MongoDB:
   ```python
   # Add note about new knowledge
   status.add_note(
       f"Added knowledge: {topic} - {brief_description}",
       "knowledge"
   )
   ```

## Knowledge Document Templates

### Pattern Template
```markdown
# [Pattern Name] Pattern

## Context
Use this pattern when [specific scenario].

## Problem
[What problem this pattern solves]

## Solution
[How the pattern works]

## Implementation
```python
# Concrete implementation example
class ExampleImplementation:
    def pattern_method(self):
        # Pattern in action
```

## Benefits
- [Benefit 1]
- [Benefit 2]

## Trade-offs
- [Trade-off 1]
- [Trade-off 2]

## Related Patterns
- [Related pattern 1]
- [Related pattern 2]
```

### Solution Template
```markdown
# Solution: [Problem Title]

## Problem Description
[Detailed problem description]

## Root Cause
[Why this problem occurs]

## Solution
[Step-by-step solution]

## Code Example
```python
# Before (problematic code)
def problematic_function():
    # Issues here

# After (fixed code)
def fixed_function():
    # Solution implemented
```

## Prevention
[How to avoid this problem in future]

## See Also
- [Related issues]
- [Documentation links]
```

### Best Practice Template
```markdown
# Best Practice: [Topic]

## Overview
[What this best practice covers]

## The Practice
[Detailed description of the practice]

## Why It Matters
[Benefits and importance]

## How to Apply
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Examples
### Good Example
```python
# Following the best practice
```

### Bad Example
```python
# What to avoid
```

## Exceptions
[When not to follow this practice]
```

### Lesson Learned Template
```markdown
# Lesson Learned: [Title]

## What Happened
[Description of the situation]

## What We Learned
[Key takeaways]

## What We Changed
[Actions taken based on learning]

## Impact
[How this improved things]

## Recommendations
[For others facing similar situations]
```

## Categories for Organization

Create subdirectories for different types:
```
dev-knowledge-base/docs/
├── patterns/           # Design patterns
├── solutions/          # Problem solutions
├── best-practices/     # Best practices
├── lessons-learned/    # Learnings from experience
├── architecture/       # Architecture decisions
├── performance/        # Performance optimizations
├── security/          # Security practices
├── integrations/      # Third-party integrations
└── troubleshooting/   # Debug solutions
```

## Examples

### Adding a Caching Pattern
```bash
cat > dev-knowledge-base/docs/patterns/content-based-caching-2024-01-15.md << 'EOF'
# Content-Based Cache Key Pattern

## Context
When caching API responses where the same content might be requested by different users or sessions.

## Solution
Use content-based cache keys instead of user-based keys.

## Implementation
```python
import hashlib

def generate_cache_key(service: str, params: dict) -> str:
    # Sort params for consistency
    sorted_params = json.dumps(params, sort_keys=True)
    # Create hash of content
    content_hash = hashlib.sha256(sorted_params.encode()).hexdigest()
    return f"{service}:{content_hash}"
```

## Benefits
- 30-60% better cache hit rate
- Reduced API costs
- Works across users

## References
- Implemented in: services/backend/utils/cache.py
- VideoCommentator: Used same pattern
EOF
```

### Adding a Performance Solution
```bash
cat > dev-knowledge-base/docs/solutions/celery-memory-leak-2024-01-15.md << 'EOF'
# Solution: Celery Worker Memory Leaks

## Problem
Celery workers consuming increasing memory over time, eventually crashing.

## Root Cause
Workers holding onto large objects between tasks.

## Solution
Configure worker recycling and memory limits:

```python
# In celery_app.py
app.conf.update(
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=2048000  # 2GB
)
```

## Prevention
- Always clean up large objects
- Use weak references where appropriate
- Monitor memory usage

## References
- Fixed in: services/backend/celery_app.py
- Monitoring: utils/memory_monitor.py
EOF
```

## Validation Checklist

Before adding knowledge, ensure:
- [ ] It's not already documented
- [ ] It's generally applicable (not one-off)
- [ ] Code examples are tested
- [ ] Benefits are clear
- [ ] Context is well-defined
- [ ] It follows project patterns

## Example Usage
```bash
# After implementing new pattern
./dev-cli prompt knowledge-add --type "pattern" --component "video_processing"

# After solving complex bug
./dev-cli prompt knowledge-add --type "solution" --component "celery_workers"

# After performance optimization
./dev-cli prompt knowledge-add --type "performance" --component "mongodb_queries"
```

## Related Prompts
- `knowledge-query` - Search existing knowledge
- `bug` - Document bug solutions
- `impl-plan` - Reference when planning
- `status-update` - Note knowledge additions