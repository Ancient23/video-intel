# Provider Integration Template

## Description
Add a new AI/ML provider integration to the Video Intelligence Platform.

## When to Use
- Integrating new video analysis provider (OpenAI, Google, etc.)
- Adding new capability provider
- Extending existing provider support
- Creating custom provider implementation

## Prerequisites
- Provider API credentials
- Understanding of provider capabilities
- Base analyzer pattern knowledge
- Cost model for the provider

## Input Required
- **Provider**: AWS Rekognition/NVIDIA/OpenAI/Google/Custom
- **Service**: chunking/analysis/embedding/etc.
- **Capabilities**: What the provider can do

## Pre-Implementation

1. Check existing provider patterns:
   ```bash
   ./dev-cli ask "Provider abstraction pattern"
   ./dev-cli ask "[provider] integration examples"
   ```

2. Review VideoCommentator patterns:
   - Factory pattern from old code
   - Cost tracking implementation
   - Error handling patterns
   - Capability-based design

3. Study base analyzer:
   - Review `services/backend/services/analysis/base_analyzer.py`
   - Understand required methods
   - Note abstract methods to implement

## Implementation Steps

### 1. Create Provider Class

Location: `services/backend/services/analysis/providers/[provider].py`

```python
"""
[Provider] Provider for video analysis
"""
import os
import time
from typing import List, Dict, Any, Optional
import structlog

from ..base_analyzer import BaseAnalyzer
from ....schemas.analysis import (
    ChunkInfo, AnalysisConfig, AnalysisResult,
    SceneDetection, ObjectDetection, ProviderType
)

logger = structlog.get_logger()


class [Provider]Analyzer(BaseAnalyzer):
    """[Provider] implementation for video analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("[PROVIDER]_API_KEY"))
        self.provider_type = ProviderType.[PROVIDER]
        self.base_url = "[provider_api_url]"
        
    async def analyze_chunk(
        self,
        chunk: ChunkInfo,
        config: AnalysisConfig
    ) -> AnalysisResult:
        """Analyze video chunk using [Provider]"""
        start_time = time.time()
        
        if not self.validate_chunk(chunk):
            return self.handle_error(ValueError("Invalid chunk"), chunk)
        
        try:
            # Provider-specific implementation
            result = await self._call_provider_api(chunk, config)
            
            # Parse results
            analysis_result = self._parse_results(result, chunk)
            
            # Add metadata
            analysis_result.processing_time = time.time() - start_time
            analysis_result.total_cost = self._calculate_cost(chunk, config)
            
            return analysis_result
            
        except Exception as e:
            return self.handle_error(e, chunk)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return provider capabilities"""
        return {
            "provider": self.provider_type.value,
            "supported_goals": [
                # List supported AnalysisGoal values
            ],
            "max_video_size_gb": 10,
            "supports_custom_prompts": True,
            "cost_per_minute": 1.0,
            "features": [
                # List specific features
            ]
        }
    
    def estimate_cost(
        self,
        duration_seconds: float,
        config: AnalysisConfig
    ) -> float:
        """Estimate cost for analysis"""
        # Provider-specific cost calculation
        return duration_seconds * self.cost_per_second
```

### 2. Add to Provider Type Enum

Edit `services/backend/schemas/analysis.py`:

```python
class ProviderType(str, Enum):
    # ... existing providers ...
    [PROVIDER] = "[provider]"
```

### 3. Update Provider Factory

Edit `services/backend/services/analysis/factory.py`:

```python
from .providers.[provider] import [Provider]Analyzer

class ProviderFactory:
    @staticmethod
    def create_provider(provider_type: ProviderType) -> BaseAnalyzer:
        # ... existing cases ...
        elif provider_type == ProviderType.[PROVIDER]:
            return [Provider]Analyzer()
```

### 4. Add Configuration

Create environment variables:
```bash
# In .env
[PROVIDER]_API_KEY=your_key
[PROVIDER]_ENDPOINT=https://api.[provider].com/v1
[PROVIDER]_RATE_LIMIT=100  # requests per minute
```

### 5. Implement Required Methods

#### API Call Method
```python
async def _call_provider_api(
    self,
    chunk: ChunkInfo,
    config: AnalysisConfig
) -> Dict[str, Any]:
    """Call provider API with chunk data"""
    # Prepare request based on provider requirements
    # Handle authentication
    # Make API call
    # Return raw response
```

#### Results Parser
```python
def _parse_results(
    self,
    response: Dict[str, Any],
    chunk: ChunkInfo
) -> AnalysisResult:
    """Parse provider response into standard format"""
    result = self.create_result("", chunk)
    
    # Parse provider-specific response format
    # Extract scenes, objects, captions, etc.
    # Normalize confidence scores
    # Add provider metadata
    
    return result
```

#### Cost Calculation
```python
def _calculate_cost(
    self,
    chunk: ChunkInfo,
    config: AnalysisConfig
) -> float:
    """Calculate actual cost for this chunk"""
    # Based on:
    # - Chunk duration
    # - Number of API calls
    # - Features used
    # - Provider pricing model
```

### 6. Add Provider-Specific Features

```python
# If provider has unique capabilities
async def [unique_feature](self, params: Dict) -> Any:
    """Provider-specific feature implementation"""
    # Custom implementation
```

## Testing

### Unit Tests
Create `services/backend/tests/test_analysis/test_[provider]_analyzer.py`:

```python
import pytest
from unittest.mock import Mock, patch
from services.analysis.providers.[provider] import [Provider]Analyzer

class Test[Provider]Analyzer:
    @pytest.fixture
    def analyzer(self):
        return [Provider]Analyzer(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_analyze_chunk(self, analyzer):
        # Mock API response
        # Test chunk analysis
        # Verify result format
    
    def test_get_capabilities(self, analyzer):
        capabilities = analyzer.get_capabilities()
        assert "supported_goals" in capabilities
        assert capabilities["provider"] == "[provider]"
    
    def test_estimate_cost(self, analyzer):
        cost = analyzer.estimate_cost(60.0, config)
        assert cost > 0
```

### Integration Tests
```python
@pytest.mark.integration
async def test_real_api_call():
    # Test with real API (use test account)
    # Verify response handling
    # Check error scenarios
```

## Documentation

### Provider Documentation
Create `docs/providers/[provider].md`:

```markdown
# [Provider] Integration

## Overview
[Provider description and capabilities]

## Configuration
- API Key: `[PROVIDER]_API_KEY`
- Endpoint: `[PROVIDER]_ENDPOINT`
- Rate Limits: X requests/minute

## Supported Features
- Feature 1: Description
- Feature 2: Description

## Cost Model
- Base rate: $X per minute
- Additional features: pricing

## Usage Examples
```python
# Example code
```

## Limitations
- Max file size: X GB
- Supported formats: mp4, avi, etc.
```

## Post-Implementation

1. Update provider orchestrator to include new provider
2. Add to API documentation
3. Create usage examples
4. Update cost comparison docs
5. Add to knowledge base:
   ```bash
   ./dev-cli prompt knowledge-add --type "integration"
   ```

## Common Patterns

### Rate Limiting
```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3)
)
async def _call_with_retry(self, *args):
    # API call with automatic retry
```

### Batch Processing
```python
async def _process_batch(self, items: List) -> List:
    # If provider supports batch operations
    # Group items efficiently
    # Handle partial failures
```

### Caching Integration
```python
from utils import cache_api_call

@cache_api_call(service=self.provider_type.value)
async def _cached_analysis(self, params):
    # Expensive operations cached automatically
```

## Checklist

- [ ] Provider class created and tested
- [ ] Added to ProviderType enum
- [ ] Factory updated
- [ ] Environment variables documented
- [ ] Unit tests written
- [ ] Integration tests completed
- [ ] Documentation created
- [ ] Cost model verified
- [ ] Error handling robust
- [ ] Caching implemented
- [ ] Knowledge base updated

## Related Prompts
- `impl-plan` - Plan provider implementation
- `test` - Add provider tests
- `knowledge-add` - Document patterns
- `status-update` - Update project status