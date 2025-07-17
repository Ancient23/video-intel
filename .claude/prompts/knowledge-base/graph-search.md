# Advanced Graph-RAG Search

## Description
Perform advanced searches using the Graph-RAG system to find implementation patterns, best practices, and architectural guidance.

## When to Use
- Before implementing any new component
- When investigating technical decisions
- Finding NVIDIA Blueprint patterns
- Exploring technology relationships
- Understanding cost implications

## Search Strategies

### 1. Implementation Patterns
```bash
# Find how to implement a specific component
./dev-cli search "[component] implementation"
./dev-cli search "NVIDIA Blueprint [component]"
./dev-cli search "[component] architecture patterns"

# Example: Video chunking
./dev-cli search "video chunking implementation"
./dev-cli search "NVIDIA Blueprint video segmentation"
./dev-cli search "FFmpeg chunking patterns"
```

### 2. Best Practices
```bash
# Find best practices for a technology
./dev-cli search "[technology] best practices"
./dev-cli search "[technology] common pitfalls"
./dev-cli search "[technology] performance optimization"

# Example: Celery
./dev-cli search "Celery canvas best practices"
./dev-cli search "Celery distributed processing patterns"
./dev-cli search "Celery error handling"
```

### 3. Cost Optimization
```bash
# Find cost optimization strategies
./dev-cli search "[service] cost optimization"
./dev-cli search "inference cost reduction"
./dev-cli search "data flywheel patterns"

# Example: ML inference
./dev-cli search "NVIDIA data flywheel"
./dev-cli search "inference caching strategies"
./dev-cli search "batch processing cost optimization"
```

### 4. Technology Relationships
```bash
# Explore how technologies work together
./dev-cli explore "[technology]" --depth 2
./dev-cli explore "[technology]" --depth 3

# Example: Qdrant
./dev-cli explore "Qdrant" --depth 2
# Shows: Qdrant -> embeddings, vector search, Graph-RAG, etc.
```

### 5. Architecture Decisions
```bash
# Find architectural patterns
./dev-cli search "two-phase pipeline architecture"
./dev-cli search "ingestion phase patterns"
./dev-cli search "retrieval phase optimization"
```

## Advanced Search Techniques

### Combining Vector and Graph Search
```bash
# Use both vector similarity and graph relationships
./dev-cli search "video processing" --use-graph
./dev-cli search "RAG implementation" --use-graph
```

### No-Graph Search (Vector Only)
```bash
# Sometimes you want just vector similarity
./dev-cli search "specific error message" --no-graph
./dev-cli search "exact code pattern" --no-graph
```

### Entity Exploration
```bash
# Deep dive into a specific entity
./dev-cli explore "MongoDB" --depth 3
./dev-cli explore "AWS Rekognition" --depth 2
./dev-cli explore "Graph-RAG" --depth 3
```

## Interpreting Results

### Vector Matches
- Based on semantic similarity
- Good for finding conceptually related content
- Look at the relevance score

### Graph Relationships
- Based on explicit connections
- Shows how technologies/concepts relate
- Reveals hidden dependencies

### Combined Results
- Best of both approaches
- Vector finds similar content
- Graph adds context and relationships

## Search Workflow

1. **Start Broad**
   ```bash
   ./dev-cli search "video analysis"
   ```

2. **Narrow Down**
   ```bash
   ./dev-cli search "video analysis provider implementation"
   ```

3. **Explore Relationships**
   ```bash
   ./dev-cli explore "video analysis provider" --depth 2
   ```

4. **Ask Specific Questions**
   ```bash
   ./dev-cli ask "How to implement video analysis provider with cost tracking?"
   ```

## Common Search Patterns

### For New Features
```bash
./dev-cli search "[feature] implementation patterns"
./dev-cli search "NVIDIA Blueprint [feature]"
./dev-cli explore "[main technology]" --depth 2
```

### For Debugging
```bash
./dev-cli search "[error message]"
./dev-cli search "[component] common issues"
./dev-cli explore "[failing component]" --depth 2
```

### For Optimization
```bash
./dev-cli search "[component] optimization"
./dev-cli search "[component] performance patterns"
./dev-cli search "cost reduction [component]"
```

### For Architecture
```bash
./dev-cli search "architectural patterns [domain]"
./dev-cli search "NVIDIA Blueprint architecture"
./dev-cli explore "[architecture pattern]" --depth 3
```

## Tips

1. **Use Quotes for Phrases**
   ```bash
   ./dev-cli search "two-phase pipeline"
   ```

2. **Try Different Terms**
   - Implementation vs Development
   - Pattern vs Architecture
   - Best practices vs Guidelines

3. **Check Entity Names**
   ```bash
   ./dev-cli info  # Shows top entities
   ```

4. **Combine Commands**
   ```bash
   # Search then explore
   ./dev-cli search "Celery patterns" && \
   ./dev-cli explore "Celery" --depth 2
   ```

## Related Prompts
- `knowledge-add` - Add new patterns to knowledge base
- `impl-plan` - Use search results for implementation
- `feature` - Apply patterns to new features