# Test Implementation

## Description
Add comprehensive tests for components and services in the Video Intelligence Platform.

## When to Use
- After implementing new features
- When fixing bugs (regression tests)
- To improve code coverage
- Before refactoring
- For critical business logic

## Prerequisites
- Component/service to test exists
- Understanding of expected behavior
- Test environment configured
- pytest installed

## Input Required
- **Component**: What to test
- **Test Types**: unit/integration/e2e
- **Coverage Goal**: Target coverage percentage

## Steps

1. Review existing test patterns:
   ```bash
   ./dev-cli ask "Testing patterns for [component type]"
   ./dev-cli ask "Test examples from VideoCommentator"
   ```

2. Check VideoCommentator test examples:
   - Look for similar component tests
   - Copy test structure
   - Note mocking patterns

3. Analyze current coverage:
   ```bash
   # Generate coverage report
   pytest --cov=services.backend --cov-report=html
   open htmlcov/index.html
   
   # Check specific module
   pytest --cov=services.backend.services.[component] --cov-report=term-missing
   ```

4. Create test structure:
   ```
   services/backend/tests/
   ├── test_[component]/
   │   ├── __init__.py
   │   ├── test_service.py
   │   ├── test_api.py
   │   └── test_integration.py
   ├── fixtures/
   │   └── [component]_fixtures.py
   └── conftest.py
   ```

5. Write tests covering:
   - Happy path scenarios
   - Error conditions
   - Edge cases
   - MongoDB interactions
   - Provider mocking (if applicable)
   - Celery task execution (if async)

6. Run tests and verify:
   ```bash
   # Run specific test file
   pytest tests/test_[component].py -v
   
   # Run with debugging
   pytest tests/test_[component].py -v -s
   
   # Run specific test
   pytest tests/test_[component].py::TestClass::test_method -v
   ```

7. Update knowledge base with test patterns

## Test Templates

### Unit Test Structure
```python
# services/backend/tests/test_[component]/test_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from ...services.[component] import [Component]Service
from ...schemas import [Component]Schema
from ...models import [Component]Model

class Test[Component]Service:
    """Unit tests for [Component]Service"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return [Component]Service()
    
    @pytest.fixture
    def mock_model(self):
        """Create mock model"""
        model = Mock(spec=[Component]Model)
        model.id = "test_id"
        model.save = AsyncMock()
        return model
    
    @pytest.mark.asyncio
    async def test_create_[component]_success(self, service, mock_model):
        """Test successful creation"""
        # Arrange
        data = [Component]Schema(
            field1="value1",
            field2="value2"
        )
        
        with patch('[Component]Model.create', return_value=mock_model):
            # Act
            result = await service.create_[component](data)
            
            # Assert
            assert result.id == "test_id"
            mock_model.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_[component]_validation_error(self, service):
        """Test validation error handling"""
        # Arrange
        invalid_data = [Component]Schema(field1="")  # Invalid
        
        # Act & Assert
        with pytest.raises(ValueError, match="field1 cannot be empty"):
            await service.create_[component](invalid_data)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test error handling"""
        with patch('[Component]Model.create', side_effect=Exception("DB Error")):
            with pytest.raises(ServiceError):
                await service.create_[component](valid_data)
```

### Integration Test
```python
# services/backend/tests/test_[component]/test_integration.py
import pytest
from ...models import [Component]Model
from ...services.[component] import [Component]Service
from ...core.database import init_database, Database

@pytest.mark.integration
class Test[Component]Integration:
    """Integration tests with real MongoDB"""
    
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        """Setup and cleanup for each test"""
        await init_database(test=True)
        yield
        # Cleanup
        await [Component]Model.delete_all()
        await Database.disconnect()
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow with real database"""
        # Create
        service = [Component]Service()
        data = {"field": "value"}
        result = await service.create(data)
        
        # Verify in database
        from_db = await [Component]Model.get(result.id)
        assert from_db.field == "value"
        
        # Update
        await service.update(result.id, {"field": "new_value"})
        
        # Verify update
        updated = await [Component]Model.get(result.id)
        assert updated.field == "new_value"
```

### API Test
```python
# services/backend/tests/test_[component]/test_api.py
import pytest
from fastapi.testclient import TestClient
from ...main import app

class Test[Component]API:
    """API endpoint tests"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_create_endpoint(self, client, mock_auth):
        """Test POST /[component]"""
        # Arrange
        payload = {
            "field1": "value1",
            "field2": "value2"
        }
        
        # Act
        response = client.post(
            "/api/v1/[component]",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["field1"] == "value1"
        assert "id" in data
    
    def test_validation_error(self, client, mock_auth):
        """Test validation error response"""
        response = client.post(
            "/api/v1/[component]",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
        assert "validation error" in response.json()["detail"]
```

### Async/Celery Test
```python
# services/backend/tests/test_[component]/test_tasks.py
import pytest
from unittest.mock import patch
from ...workers.[component]_tasks import process_[component]_async

class Test[Component]Tasks:
    """Celery task tests"""
    
    @pytest.mark.asyncio
    async def test_async_processing(self, celery_app, celery_worker):
        """Test async task execution"""
        # Arrange
        task_data = {"id": "test_123"}
        
        # Act
        result = process_[component]_async.delay(task_data)
        
        # Wait for result
        task_result = result.get(timeout=10)
        
        # Assert
        assert task_result["status"] == "completed"
        assert "result" in task_result
```

## Test Fixtures

### Common Fixtures
```python
# services/backend/tests/conftest.py
import pytest
from datetime import datetime

@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime.now()"""
    class MockDateTime:
        @staticmethod
        def now():
            return datetime(2024, 1, 1, 12, 0, 0)
    
    monkeypatch.setattr("datetime.datetime", MockDateTime)

@pytest.fixture
def mock_s3_client(monkeypatch):
    """Mock S3 client"""
    mock = Mock()
    mock.upload_file = Mock()
    mock.download_file = Mock()
    monkeypatch.setattr("boto3.client", lambda *args: mock)
    return mock

@pytest.fixture
async def test_video():
    """Create test video"""
    from ..models import Video
    video = Video(
        title="Test Video",
        s3_uri="s3://test-bucket/test.mp4",
        duration=120.0
    )
    await video.create()
    yield video
    await video.delete()
```

## Coverage Goals

| Component Type | Target Coverage |
|---------------|----------------|
| Core Services | 90%+ |
| API Endpoints | 85%+ |
| Utilities | 95%+ |
| Workers/Tasks | 80%+ |
| Models | 90%+ |

## Best Practices

1. **Test Naming**: Use descriptive names
   - `test_should_create_video_when_valid_data_provided`
   - `test_should_raise_error_when_s3_uri_invalid`

2. **AAA Pattern**: Arrange, Act, Assert
   ```python
   # Arrange - setup
   data = create_test_data()
   
   # Act - execute
   result = service.process(data)
   
   # Assert - verify
   assert result.status == "success"
   ```

3. **Mock External Dependencies**:
   - Database calls (for unit tests)
   - API calls
   - File system operations
   - Time-dependent operations

4. **Use Fixtures**: DRY principle
   - Reusable test data
   - Common mocks
   - Setup/teardown logic

5. **Test Edge Cases**:
   - Empty inputs
   - None values
   - Maximum values
   - Concurrent operations

## Example Usage
```bash
# Add tests for video chunking service
./dev-cli prompt test --component "video_chunking" --coverage 90

# Add integration tests
./dev-cli prompt test --component "api" --type "integration"
```

## Related Prompts
- `bug` - Write regression tests after fixes
- `feature` - Test new features
- `impl-plan` - Include test planning
- `debt-add` - Track missing test coverage