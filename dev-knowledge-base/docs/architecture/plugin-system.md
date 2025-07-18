# Plugin System Architecture

## Overview

The Video Intelligence Platform uses a plugin-based architecture for temporal marker detection and audio transcription. This allows for flexible provider integration without modifying core code.

## Key Design Principles

### 1. Provider Agnostic
- Core system doesn't depend on specific providers
- Easy to add new providers (AWS, NVIDIA, OpenAI, etc.)
- Consistent interface across all providers

### 2. Plugin Types

#### Temporal Marker Plugins
Detect interesting timestamps in videos:
- Shot boundaries
- Object appearances
- Scene changes
- Custom events based on prompts

#### Transcription Plugins
Convert audio to text with metadata:
- Full transcription with timestamps
- Speaker diarization
- Language detection
- Custom vocabularies

### 3. Plugin Interface

```python
# Temporal Marker Plugin
class BaseTemporalPlugin(ABC):
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Plugin capabilities and metadata"""
        
    @abstractmethod
    async def detect_markers(
        self, chunk: ChunkInfo, config: AnalysisConfig
    ) -> List[TemporalMarker]:
        """Detect markers in video chunk"""

# Transcription Plugin  
class BaseTranscriptionPlugin(ABC):
    @abstractmethod
    async def transcribe(
        self, audio_path: str, config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Transcribe audio file"""
```

## Plugin Registry

### Dynamic Loading
```python
# Registry automatically discovers plugins
registry = TemporalMarkerRegistry()
registry.discover_plugins("./temporal_markers/")

# Get plugin by name
plugin = registry.get_plugin("aws_rekognition")

# Get plugins by capability
shot_detectors = registry.get_by_capability("shot_detection")
```

### Capability-Based Selection
```python
# Orchestrator selects best plugin for task
plugin = registry.select_plugin(
    required_features=["shot_detection", "object_tracking"],
    preferred_cost=0.001,  # $/second
    chunk_duration=30
)
```

## Implementation Examples

### AWS Rekognition Plugin
```python
class AWSRekognitionPlugin(BaseTemporalPlugin):
    def get_plugin_info(self):
        return {
            "plugin_name": "aws_rekognition",
            "plugin_version": "1.0.0",
            "supported_events": [
                "shot_boundary",
                "object_appearance",
                "scene_change",
                "technical_cue"
            ],
            "requires_s3": True,
            "max_chunk_duration": 30,
            "cost_per_minute": 1.0
        }
```

### NVIDIA VILA Plugin
```python
class NVIDIAVilaPlugin(BaseTemporalPlugin):
    def get_plugin_info(self):
        return {
            "plugin_name": "nvidia_vila",
            "plugin_version": "1.0.0",
            "supported_events": [
                "custom_prompt",
                "action_detection",
                "scene_understanding"
            ],
            "requires_gpu": True,
            "max_chunk_duration": 20,
            "cost_per_minute": 0.21  # Based on frames
        }
```

## Multi-Provider Orchestration

### Parallel Execution
```python
# Run multiple plugins in parallel
async def analyze_with_plugins(chunk, plugins):
    tasks = [
        plugin.detect_markers(chunk, config) 
        for plugin in plugins
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return merge_results(results)
```

### Fallback Handling
```python
# Primary plugin with fallback
try:
    markers = await primary_plugin.detect_markers(chunk)
except PluginError:
    markers = await fallback_plugin.detect_markers(chunk)
```

## Cost Optimization

### Cost Tracking
```python
# Each plugin reports its cost
cost = plugin.estimate_cost(duration_seconds=30)

# Registry tracks cumulative costs
total_cost = registry.get_total_cost(video_id)
```

### Smart Selection
```python
# Choose cheapest plugin that meets requirements
plugin = registry.select_optimal_plugin(
    required_accuracy=0.85,
    max_cost_per_minute=0.50
)
```

## S3 Multi-Tenancy

### Path Structure
```
{S3_BUCKET}/projects/{project_id}/videos/{video_id}/
├── chunks/          # Video chunks
├── keyframes/       # Extracted frames
├── transcripts/     # Audio transcripts
└── metadata/        # Analysis results

{S3_OUTPUT_BUCKET}/projects/{project_id}/
├── memories/        # Processed results
├── compilations/    # Generated videos
└── exports/         # User downloads
```

### Environment Variables
- `S3_BUCKET`: Primary storage for ingestion
- `S3_OUTPUT_BUCKET`: Output storage for retrieval

## Progress Reporting

### Celery Task Phases
```python
class IngestionPhase(Enum):
    INITIALIZING = "initializing"
    CHUNKING = "chunking"
    ANALYZING_TEMPORAL = "analyzing_temporal"
    TRANSCRIBING_AUDIO = "transcribing_audio"
    BUILDING_MEMORY = "building_memory"
    FINALIZING = "finalizing"
```

### Real-time Updates
```python
# Report progress with metadata
task.update_state(
    state='PROGRESS',
    meta={
        'current_phase': 'analyzing_temporal',
        'phase_progress': 45.5,
        'providers_active': ['aws_rekognition'],
        'markers_detected': 156
    }
)
```

## Best Practices

### 1. Plugin Development
- Follow base class interface strictly
- Include comprehensive error handling
- Provide accurate cost estimates
- Document all capabilities

### 2. Resource Management
- Clean up temporary files
- Respect chunk duration limits
- Handle API rate limits gracefully
- Cache results when appropriate

### 3. Testing
- Unit test each plugin independently
- Integration test with orchestrator
- Test fallback scenarios
- Verify cost calculations

## Future Extensions

### 1. Plugin Marketplace
- Community-contributed plugins
- Plugin certification process
- Version management
- Dependency resolution

### 2. Advanced Features
- Plugin composition (combine multiple)
- Custom plugin chains
- A/B testing frameworks
- Performance benchmarking

### 3. Enhanced Capabilities
- Real-time streaming support
- Edge deployment options
- Federated learning integration
- Privacy-preserving analysis