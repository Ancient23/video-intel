# Pattern Compliance Check

## Description
Verify that your implementation follows established patterns from the Graph-RAG knowledge base, especially NVIDIA Blueprint patterns.

## When to Use
- Before committing new code
- During code review
- When implementing critical components
- Before marking a task complete

## Steps

### 1. Identify Patterns to Check
```bash
# Search for relevant patterns
./dev-cli search "[component] best practices"
./dev-cli search "NVIDIA Blueprint [component]"
./dev-cli search "[component] anti-patterns"
```

### 2. Extract Key Requirements
From the search results, identify:
- Required architectural patterns
- Naming conventions
- Error handling approaches
- Performance considerations
- Cost optimization strategies

### 3. Compare Implementation

#### Architecture Check
```bash
# Does your implementation follow the two-phase pattern?
./dev-cli search "two-phase pipeline architecture"

# Check against found patterns:
- [ ] Ingestion phase properly separated
- [ ] Retrieval phase optimized
- [ ] Proper abstraction layers
```

#### Provider Pattern Check
```bash
# If implementing a provider
./dev-cli search "provider abstraction pattern"

# Verify:
- [ ] Uses ProviderFactory
- [ ] Implements base interface
- [ ] Has cost tracking
- [ ] Includes retry logic
```

#### Error Handling Check
```bash
# Search for error patterns
./dev-cli search "[component] error handling"

# Ensure:
- [ ] Proper exception types
- [ ] Retry mechanisms
- [ ] Logging with context
- [ ] User-friendly error messages
```

#### Performance Check
```bash
# Search for optimization patterns
./dev-cli search "[component] performance optimization"

# Validate:
- [ ] Batch processing where applicable
- [ ] Proper caching strategy
- [ ] Memory limits set
- [ ] Async operations used correctly
```

### 4. Cost Compliance
```bash
# Check cost optimization patterns
./dev-cli search "cost optimization [service]"
./dev-cli ask "Cost implications of [approach]"

# Verify:
- [ ] Cost tracking implemented
- [ ] Batch operations for efficiency
- [ ] Caching to reduce API calls
- [ ] Alternative providers considered
```

### 5. Generate Compliance Report

```markdown
## Pattern Compliance Report

### Component: [Component Name]

#### Patterns Followed ✅
- Two-phase architecture
- Provider abstraction pattern
- Async operation handling

#### Patterns Violated ❌
- Missing cost tracking
- No retry logic for external calls

#### Recommendations
1. Add cost tracking using pattern from knowledge base
2. Implement retry with exponential backoff

#### Knowledge Base References
- [Link to relevant pattern docs]
- NVIDIA Blueprint section X.Y
```

## Common Patterns to Check

### Video Processing
```bash
./dev-cli search "video chunking patterns"
./dev-cli search "FFmpeg best practices"
./dev-cli search "shot detection patterns"
```

### API Development
```bash
./dev-cli search "FastAPI patterns"
./dev-cli search "API error handling"
./dev-cli search "async endpoint patterns"
```

### Database Operations
```bash
./dev-cli search "MongoDB query patterns"
./dev-cli search "connection pooling"
./dev-cli search "transaction patterns"
```

### Task Processing
```bash
./dev-cli search "Celery canvas patterns"
./dev-cli search "task retry strategies"
./dev-cli search "progress tracking patterns"
```

## Anti-Pattern Detection

Search for what NOT to do:
```bash
./dev-cli search "[component] anti-patterns"
./dev-cli search "common mistakes [technology]"
./dev-cli ask "What to avoid when implementing [component]"
```

## Automated Checking

Future enhancement - add to CI/CD:
```python
# scripts/check_patterns.py
import subprocess
import json

def check_pattern_compliance(component):
    # Search for patterns
    result = subprocess.run(
        ["./dev-cli", "search", f"{component} patterns"],
        capture_output=True,
        text=True
    )
    
    # Parse and check against code
    # Generate report
    # Return pass/fail
```

## Example Usage

```bash
# Check video chunking implementation
./dev-cli prompt pattern-check --component "video_chunking"

# Check API endpoint compliance
./dev-cli prompt pattern-check --component "analyze_endpoint"

# Check provider implementation
./dev-cli prompt pattern-check --component "rekognition_provider"
```

## Related Prompts
- `impl-plan` - Plan with patterns upfront
- `feature` - Implement with patterns
- `debt-add` - Document pattern violations
- `knowledge-add` - Add new patterns discovered