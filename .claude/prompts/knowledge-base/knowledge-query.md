# Development Knowledge Base Query

## Description
Query the development knowledge base for patterns, solutions, and implementation guidance.

## When to Use
- Before implementing new features
- When facing implementation decisions
- Looking for existing patterns
- Troubleshooting issues
- Checking best practices

## Prerequisites
- Virtual environment activated
- Knowledge base initialized
- Qdrant and Neo4j running

## Query Types

### Pattern Queries (Graph-RAG Enhanced)
```bash
# Implementation patterns - Use search for better results
./dev-cli search "[component] implementation patterns"
./dev-cli search "NVIDIA Blueprint [component]"
./dev-cli ask "How to implement [component]"

# Architecture patterns with graph exploration
./dev-cli search "architecture patterns [system]"
./dev-cli explore "[architecture pattern]" --depth 2
./dev-cli ask "How to structure [component]"
```

### Problem-Solution Queries
```bash
# Issues and solutions
./dev-cli ask "Issues with [component]"
./dev-cli ask "How to handle [error]"
./dev-cli ask "Problems with [integration]"

# Performance
./dev-cli ask "Optimize [operation]"
./dev-cli ask "Performance issues with [feature]"
```

### Technology and Pattern Reference
```bash
# Search for specific implementations
./dev-cli search "[technology] implementation examples"
./dev-cli search "production [component] patterns"
./dev-cli explore "[technology]" --depth 2

# NVIDIA Blueprint patterns
./dev-cli search "NVIDIA Blueprint [feature]"
./dev-cli ask "NVIDIA video processing patterns"
```

### Cost and Optimization
```bash
# Cost optimization
./dev-cli ask "Reduce costs for [operation]"
./dev-cli ask "Cost-effective [feature] implementation"
./dev-cli ask "Provider cost comparison"
```

## Steps

1. **Start with Graph-RAG search** (MANDATORY):
   ```bash
   source venv/bin/activate
   ./dev-cli search "[your topic]"
   ./dev-cli explore "[main technology]" --depth 2
   ```

2. **Then ask specific questions**:
   ```bash
   ./dev-cli ask "[your specific question]"
   ```

3. **For implementation suggestions**:
   ```bash
   ./dev-cli suggest "[component name]"
   ```

4. Check multiple related topics:
   - NVIDIA Blueprint patterns (PRIORITY)
   - Infrastructure best practices
   - Cost optimization strategies
   - Known issues and solutions
   - Technology relationships

5. If no results found:
   - Try different search terms
   - Use entity exploration
   - Check PRD for specifications
   - Review MongoDB schemas

## Query Strategies

### Broad to Specific
```bash
# Start broad
./dev-cli ask "video processing"

# Get more specific based on results
./dev-cli ask "video chunking with FFmpeg"

# Very specific
./dev-cli ask "FFmpeg memory optimization for large videos"
```

### Component-Based
```bash
# By component
./dev-cli ask "celery configuration"
./dev-cli ask "mongodb schema design"
./dev-cli ask "redis caching patterns"
```

### Problem-Based
```bash
# By problem
./dev-cli ask "memory leaks in video processing"
./dev-cli ask "slow MongoDB queries"
./dev-cli ask "API rate limiting"
```

## Understanding Results

### Result Format
```
Query: How to implement video chunking

Results:
1. [Document Title] - Relevance: 0.92
   Summary of the pattern or solution...
   
2. [Another Document] - Relevance: 0.87
   Additional information...
```

### Interpreting Relevance
- **0.9+**: Highly relevant, directly applicable
- **0.8-0.9**: Very relevant, minor adaptation needed
- **0.7-0.8**: Relevant, requires some modification
- **<0.7**: Tangentially related, use with caution

## Advanced Queries

### Multi-Topic Queries
```bash
# Combine topics
./dev-cli ask "celery tasks with mongodb progress tracking"
./dev-cli ask "AWS Rekognition cost optimization strategies"
```

### Comparison Queries
```bash
# Compare approaches
./dev-cli ask "Redis vs MongoDB for caching"
./dev-cli ask "NVIDIA VILA vs AWS Rekognition for scene detection"
```

### Integration Queries
```bash
# How components work together
./dev-cli ask "Celery and MongoDB integration patterns"
./dev-cli ask "S3 and Redis caching strategy"
```

## Troubleshooting

### No Results Found
1. Try different keywords
2. Break down complex queries
3. Check spelling
4. Use synonyms

### Too Many Results
1. Add more specific terms
2. Include component names
3. Specify the context

### Irrelevant Results
1. Rephrase the question
2. Add exclusion terms
3. Query by component

## Adding Context

If results need more context:
```bash
# Add component context
./dev-cli ask "error handling in video chunking service"

# Add technology context
./dev-cli ask "MongoDB aggregation for video analytics"

# Add problem context
./dev-cli ask "handling large files in S3 uploads"
```

## Example Queries

### Feature Implementation
```bash
./dev-cli ask "How to implement knowledge graph from video analysis"
# Returns: Graph construction patterns, entity extraction methods
```

### Performance Optimization
```bash
./dev-cli ask "Optimize video processing memory usage"
# Returns: Memory monitoring, chunking strategies, worker limits
```

### Error Resolution
```bash
./dev-cli ask "Fix MongoDB connection pool exhausted"
# Returns: Connection pooling config, async patterns
```

### Best Practices
```bash
./dev-cli ask "Best practices for provider abstraction"
# Returns: Factory pattern, capability-based design
```

## Related Prompts
- `knowledge-add` - Add new knowledge
- `impl-plan` - Use query results for planning
- `bug` - Query for similar issues
- `feature` - Query for implementation patterns