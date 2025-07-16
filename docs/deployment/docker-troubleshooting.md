# Docker Troubleshooting Guide

This guide helps resolve common issues when running the Video Intelligence Platform with Docker.

## Common Issues and Solutions

### 1. Port Already in Use

**Error**: `bind: address already in use`

**Cause**: Another service (likely from VideoCommentator) is using the same port.

**Solution**:
```bash
# Find the process using the port (example for port 27017)
lsof -i :27017

# Stop conflicting containers
docker ps | grep 27017
docker stop <container_id>

# Or stop all VideoCommentator containers
docker ps | grep videocommentator | awk '{print $1}' | xargs docker stop
```

### 2. Import Errors

**Error**: `ImportError: cannot import name 'X' from 'module'`

**Common Causes**:
1. Relative imports (using `..`) instead of absolute imports
2. Class name mismatches
3. Missing dependencies

**Solutions**:

1. **Fix relative imports**:
   ```python
   # Bad
   from ..models import Video
   from ...services import SomeService
   
   # Good
   from models import Video
   from services import SomeService
   ```

2. **Check actual class names**:
   ```bash
   # Find class definitions
   grep -r "^class.*ClassName" services/backend/
   ```

3. **Add missing dependencies**:
   ```bash
   # Add to requirements.txt
   echo "package-name==version" >> requirements.txt
   
   # Rebuild containers
   docker compose build --no-cache
   ```

### 3. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'ffmpeg'`

**Solution**:
```bash
# Add to requirements.txt
echo "ffmpeg-python==0.2.0" >> requirements.txt

# Copy to backend directory
cp requirements.txt services/backend/

# Rebuild
docker compose build --no-cache
docker compose up -d
```

### 4. Database Connection Issues

**Error**: `MotorDatabase object is not callable`

**Cause**: Incorrect database initialization

**Solution**: Ensure proper database initialization:
```python
# In main.py
from core.database import Database

async def lifespan(app: FastAPI):
    await Database.connect()
    yield
    await Database.disconnect()
```

### 5. Redis Connection Refused

**Error**: `Error 111 connecting to localhost:6379. Connection refused`

**Cause**: Service trying to connect to localhost instead of Redis container

**Solution**: Use environment variables:
```python
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
```

### 6. Container Keeps Restarting

**Diagnosis**:
```bash
# Check container logs
docker logs <container_name> --tail 100

# Check exit code
docker inspect <container_name> --format='{{.State.ExitCode}}'
```

**Common Solutions**:
1. Fix import errors (see above)
2. Check environment variables
3. Ensure all dependencies are installed
4. Verify PYTHONPATH is set correctly

### 7. Flower Not Starting

**Current Status**: Flower has persistent import issues and is disabled.

**Workaround**: Monitor Celery using logs:
```bash
# View worker logs
docker compose logs -f worker

# Check task execution
docker compose exec worker celery -A celery_app inspect active
```

## Debugging Commands

### Check Service Health
```bash
# Overall status
docker compose ps

# API health
curl http://localhost:8003/health

# MongoDB connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis connection
docker compose exec redis redis-cli ping

# ChromaDB status
curl http://localhost:8000/api/v1/heartbeat
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail 100 worker

# With timestamps
docker compose logs -t api
```

### Access Containers
```bash
# Execute commands
docker compose exec api python -c "import sys; print(sys.path)"

# Interactive shell
docker compose exec api bash

# Check environment
docker compose exec api env | grep PYTHON
```

### Rebuild and Restart
```bash
# Full rebuild
docker compose down
docker compose build --no-cache
docker compose up -d

# Restart specific service
docker compose restart api

# Force recreate
docker compose up -d --force-recreate api
```

## Prevention Tips

1. **Always use absolute imports** in Python files
2. **Keep requirements.txt synchronized** between root and services/backend/
3. **Test locally** before committing
4. **Check logs immediately** after starting services
5. **Document any new dependencies** in both requirements.txt and CLAUDE.md

## Getting Help

1. Check existing patterns in VideoCommentator repository
2. Query the knowledge base: `./dev-cli ask "docker error: [your error]"`
3. Review deployment documentation in `docs/deployment/`
4. Check CLAUDE.md for recent updates and known issues

## Emergency Recovery

If all else fails:
```bash
# Stop everything
docker compose down -v

# Remove all containers and volumes
docker system prune -a --volumes

# Fresh start
docker compose build --no-cache
docker compose up -d
```

**Warning**: This will delete all local data in Docker volumes!