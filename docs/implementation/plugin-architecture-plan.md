# Plugin Architecture Implementation Plan

## Overview
This document outlines the implementation plan for creating a plugin-based architecture for temporal marker detection and audio transcription in the video intelligence platform.

## Architecture Goals
1. **Flexibility**: Easy to add new providers without modifying core code
2. **Consistency**: Uniform interface across all providers
3. **Reliability**: Graceful fallbacks and error handling
4. **Performance**: Parallel execution where possible
5. **Cost Optimization**: Track and optimize provider usage

## Implementation Steps

### Step 1: Create Base Plugin Classes (2 hours)

#### 1.1 Temporal Marker Plugin Base
Location: `services/backend/services/analysis/temporal_markers/base_temporal.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from schemas.analysis import TemporalMarker, ChunkInfo, AnalysisConfig

class BaseTemporalPlugin(ABC):
    """Base class for temporal marker detection plugins"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.plugin_info = self.get_plugin_info()
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin information and capabilities"""
        pass
    
    @abstractmethod
    async def detect_markers(
        self,
        chunk: ChunkInfo,
        config: AnalysisConfig
    ) -> List[TemporalMarker]:
        """Detect temporal markers in video chunk"""
        pass
    
    @abstractmethod
    def estimate_cost(self, duration_seconds: float) -> float:
        """Estimate cost for processing duration"""
        pass
    
    def validate_chunk(self, chunk: ChunkInfo) -> bool:
        """Validate chunk meets plugin requirements"""
        return chunk.duration <= self.plugin_info.get('max_chunk_duration', 30)
```

#### 1.2 Transcription Plugin Base
Location: `services/backend/services/analysis/transcription/base_transcription.py`

```python
class BaseTranscriptionPlugin(ABC):
    """Base class for audio transcription plugins"""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        config: TranscriptionConfig
    ) -> TranscriptionResult:
        """Transcribe audio file"""
        pass
```

### Step 2: Create Plugin Registries (2 hours)

#### 2.1 Temporal Marker Registry
Location: `services/backend/services/analysis/temporal_markers/registry.py`

Features:
- Dynamic plugin registration
- Plugin discovery from directory
- Capability-based selection
- Fallback mechanisms

#### 2.2 Transcription Registry
Location: `services/backend/services/analysis/transcription/registry.py`

### Step 3: Implement AWS Rekognition Plugin (4 hours)

#### 3.1 Refactor Existing AWS Provider
- Move temporal marker detection logic to plugin
- Implement base class interface
- Add proper cost tracking
- Handle S3 requirements

#### 3.2 Key Features
- Shot boundary detection
- Object tracking with timestamps
- Scene change detection
- Technical cue detection

### Step 4: Implement AWS Transcribe Plugin (4 hours)

#### 4.1 Create AWS Transcribe Plugin
Location: `services/backend/services/analysis/transcription/aws_transcribe_plugin.py`

Features:
- Full transcription with timestamps
- Speaker diarization
- Multiple language support
- Vocabulary customization

### Step 5: Update Orchestration Service (3 hours)

#### 5.1 Integrate Plugin System
- Replace hardcoded provider calls with plugin registry
- Dynamic plugin selection based on config
- Parallel execution of multiple plugins
- Proper error handling and fallbacks

#### 5.2 Fix Technical Debt
- Remove hardcoded provider in temporal markers (ORCH-003)
- Add retry logic for failed plugins
- Implement proper cost tracking

### Step 6: S3 Multi-Tenant Structure (2 hours)

#### 6.1 Update S3 Utils
- Add project_id to all S3 paths
- Create helper methods for path generation
- Update environment variable usage

#### 6.2 MongoDB Schema Updates
- Add s3_paths to VideoMemory
- Track project_id in all collections
- Update indices for multi-tenancy

### Step 7: Celery Status Reporting (3 hours)

#### 7.1 Create Progress Reporting System
- Define ingestion phases enum
- Create progress update methods
- Implement WebSocket notifications
- Add Redis-based progress storage

#### 7.2 Update Orchestration Task
- Report progress at each phase
- Include phase metadata
- Handle sub-task progress aggregation

### Step 8: Testing (4 hours)

#### 8.1 Unit Tests
- Plugin base class tests
- Registry functionality tests
- Individual plugin tests

#### 8.2 Integration Tests
- Full pipeline with plugins
- Fallback scenarios
- Multi-tenant S3 operations

## File Structure

```
services/backend/services/analysis/
├── temporal_markers/
│   ├── __init__.py
│   ├── base_temporal.py              # Base class
│   ├── registry.py                   # Plugin registry
│   ├── aws_rekognition_plugin.py    # AWS implementation
│   ├── nvidia_vila_plugin.py        # NVIDIA implementation
│   └── tests/
│       ├── test_base.py
│       ├── test_registry.py
│       └── test_aws_plugin.py
├── transcription/
│   ├── __init__.py
│   ├── base_transcription.py        # Base class
│   ├── registry.py                   # Plugin registry
│   ├── aws_transcribe_plugin.py     # AWS implementation
│   ├── nvidia_riva_plugin.py        # NVIDIA implementation
│   └── tests/
└── orchestration/
    ├── progress_reporter.py          # Celery progress reporting
    └── plugin_orchestrator.py        # Plugin coordination
```

## Success Criteria

1. **Plugin System Working**
   - Can dynamically load and use plugins
   - Plugins follow consistent interface
   - Registry handles plugin discovery

2. **AWS Plugins Functional**
   - AWS Rekognition detects temporal markers
   - AWS Transcribe provides transcriptions
   - Both integrate seamlessly with orchestration

3. **Multi-Tenancy Ready**
   - S3 paths include project_id
   - MongoDB tracks project ownership
   - No cross-project data leakage

4. **Progress Reporting Active**
   - Real-time updates during processing
   - Granular phase information
   - Error and warning collection

5. **Tests Passing**
   - All unit tests green
   - Integration tests cover main flows
   - Edge cases handled

## Next Steps After Implementation

1. Implement NVIDIA plugins (VILA, Riva)
2. Add OpenAI Whisper transcription
3. Create plugin marketplace/registry
4. Add plugin versioning and updates
5. Implement plugin composition (multiple plugins per task)

## Estimated Total Time: 24 hours