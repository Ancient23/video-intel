# Quick Test Reference

## 🚀 Most Common Commands

```bash
# From project root directory:

# Run all tests (Docker - recommended)
./scripts/test-docker.sh

# Run specific test file
./scripts/test-quick.sh "test_health"

# Run and watch for changes
./scripts/test-watch.sh
```

## 📍 Where to Run

- **Always from project root** when using scripts
- Scripts handle directory navigation for you
- No need to cd into services/backend

## 🔄 After Coding Changes

Just run tests! No rebuild needed:
```bash
./scripts/test-docker.sh
```

Your code changes are automatically picked up.

## 🐛 Debug a Failing Test

```bash
# Show detailed output
docker compose run --rm api python -m pytest tests/failing_test.py -vv

# Drop into debugger
docker compose run --rm api python -m pytest tests/failing_test.py --pdb
```

## 📊 Test Coverage

```bash
# Generate coverage report
./scripts/test-docker.sh

# View in browser
open test-results/htmlcov/index.html
```

## ⚡ Quick Tips

1. **Docker must be running** for test scripts
2. **Fresh shell not required** - just run from project root
3. **No Python env needed** when using Docker
4. **Auto-reloads code** - no restart needed

## 🆘 Common Issues

- **Permission denied**: `chmod +x scripts/*.sh`
- **Import errors**: You're in wrong directory
- **Connection failed**: Docker not running

## Related Documentation
Full guide: [Testing Guide](./TESTING.md)
