# Video Chunking and Analysis Test Suite

This directory contains comprehensive unit tests for the video chunking and analysis services.

## Test Files

### `test_analysis_planner.py`
Tests for the `AnalysisPlanner` service:
- Goal detection from user prompts
- Video type classification
- Provider selection logic
- Cost estimation
- Chunk duration/overlap calculation
- Custom prompt generation

### `test_video_chunker.py`
Tests for the `VideoChunker` service:
- S3 download/upload operations
- FFmpeg video processing (mocked)
- Chunk boundary calculation
- Keyframe extraction
- Temporary file management
- Error handling for video operations

### `test_provider_orchestrator.py`
Tests for the `ProviderOrchestrator` service:
- Provider initialization
- Parallel provider execution
- Result merging from multiple providers
- Cost aggregation
- Error handling for failed providers
- Provider capability queries

### `test_orchestration_service.py`
Tests for the main `VideoChunkingOrchestrationService`:
- Complete video processing workflow
- MongoDB document updates
- Job progress tracking
- Scene creation and merging
- Error handling and recovery
- Job retry functionality
- Status queries

## Running Tests

### Run all chunking tests:
```bash
pytest services/backend/tests/test_chunking/
```

### Run specific test file:
```bash
pytest services/backend/tests/test_chunking/test_analysis_planner.py
```

### Run with coverage:
```bash
pytest services/backend/tests/test_chunking/ --cov=services.chunking --cov-report=html
```

### Run specific test:
```bash
pytest services/backend/tests/test_chunking/test_video_chunker.py::TestVideoChunker::test_create_chunks_normal
```

## Test Structure

Each test file follows this pattern:
1. **Fixtures**: Reusable test data and mocked objects
2. **Success Cases**: Testing normal operation
3. **Error Cases**: Testing error handling
4. **Edge Cases**: Testing boundary conditions

## Mocking Strategy

- **External Services**: S3, MongoDB, and provider APIs are mocked
- **FFmpeg**: Video processing operations are mocked
- **Async Operations**: AsyncMock used for async methods
- **File System**: Temporary directories used for file operations

## Common Fixtures

See `../conftest.py` for shared fixtures:
- `mock_env_vars`: Environment variable setup
- `mock_boto3_client`: S3 client mock
- `mock_beanie_document`: MongoDB document mock
- `event_loop`: Async test support

## Adding New Tests

When adding tests for new functionality:
1. Create appropriate fixtures for test data
2. Mock external dependencies
3. Test both success and failure cases
4. Include edge cases
5. Ensure async methods are properly tested
6. Update this README with new test descriptions