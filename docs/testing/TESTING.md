# Testing Guide

This guide explains how to run tests for the Video Intelligence Platform.

## Quick Start (Recommended)

From the project root directory:

```bash
# Run all tests with Docker (recommended - no setup needed)
./scripts/test-docker.sh

# Run specific tests
./scripts/test-quick.sh "test_health"

# Run tests and watch for changes
./scripts/test-watch.sh
```

## Testing Options

### Option 1: Docker Testing (Recommended)
**Pros**: No setup required, consistent environment, isolated databases  
**Requirements**: Docker running

```bash
# From project root
./scripts/test-docker.sh

# Or run specific test files
docker compose run --rm api python -m pytest tests/test_api/test_health.py -v

# With coverage
docker compose run --rm api python -m pytest --cov=. --cov-report=term
```

### Option 2: Local Python Environment
**Pros**: Faster, easier debugging  
**Requirements**: Python venv, local services running

```bash
# One-time setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start required services
docker compose up -d mongodb redis

# Run tests (from project root)
cd services/backend
python -m pytest tests/ -v

# Or use the script (from project root)
./scripts/test-local.sh
```

## After Writing New Code

No special steps needed! Just run tests:

1. **With Docker**: Your code changes are automatically picked up (volume mounted)
   ```bash
   ./scripts/test-docker.sh
   ```

2. **With Python env**: Just run pytest again
   ```bash
   cd services/backend
   python -m pytest tests/test_your_new_feature.py -v
   ```

## Test Categories

```bash
# Run only unit tests
docker compose run --rm api python -m pytest -m unit

# Run only integration tests  
docker compose run --rm api python -m pytest -m integration

# Run tests for a specific component
docker compose run --rm api python -m pytest tests/test_chunking/ -v
```

## Writing Tests

1. Create test file in appropriate directory:
   - `tests/test_api/` - API endpoint tests
   - `tests/test_services/` - Service/business logic tests
   - `tests/test_models/` - Database model tests
   - `tests/test_workers/` - Celery task tests

2. Follow naming convention: `test_*.py`

3. Example test:
   ```python
   import pytest
   
   def test_my_feature():
       # Arrange
       data = {"test": "value"}
       
       # Act
       result = my_function(data)
       
       # Assert
       assert result == expected_value
   ```

## Debugging Failed Tests

```bash
# Show detailed error output
docker compose run --rm api python -m pytest tests/failing_test.py -vv --tb=short

# Drop into debugger on failure
docker compose run --rm api python -m pytest tests/failing_test.py --pdb

# Run single test method
docker compose run --rm api python -m pytest tests/test_file.py::TestClass::test_method
```

## CI/CD Testing

Tests automatically run on every push via GitHub Actions. To run the same tests locally:

```bash
./scripts/test-ci.sh
```

## Common Issues

1. **Import errors**: Ensure you're running from correct directory
2. **Database connection failed**: Check if MongoDB/Redis are running
3. **Environment variables**: Docker commands handle this automatically
4. **Permission denied on scripts**: Run `chmod +x scripts/*.sh`

## Test Coverage

View test coverage:

```bash
# Generate coverage report
./scripts/test-docker.sh

# View HTML report
open test-results/htmlcov/index.html
```

## Environment Variables

When running tests manually, these are set automatically by Docker. For Python env:

```bash
export MONGODB_URL="mongodb://localhost:27017/test"
export REDIS_URL="redis://localhost:6379/1"
export ENVIRONMENT="test"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
```

## Need Help?

- Check test examples in `tests/` directory
- See `pytest.ini` for configuration
- Run `pytest --help` for all options

## Related Documentation
- 🧪 [Quick Test Reference](./QUICK_TEST_REFERENCE.md) - Quick Reference for most commonly used testing
