#!/bin/bash
# Validate test setup is working correctly

set -e

echo "🔍 Validating test setup..."

# Check if test dependencies are installed
echo "📦 Checking test dependencies..."
docker compose run --rm api python -c "
import sys
try:
    import pytest
    print('✅ pytest installed')
except ImportError:
    print('❌ pytest not installed')
    sys.exit(1)
    
try:
    import pytest_asyncio
    print('✅ pytest-asyncio installed')
except ImportError:
    print('❌ pytest-asyncio not installed')
    sys.exit(1)
    
try:
    import fakeredis
    print('✅ fakeredis installed')
except ImportError:
    print('❌ fakeredis not installed')
    sys.exit(1)
"

# Run a simple test
echo -e "\n🧪 Running simple validation test..."
docker compose run --rm api python -c "
import os
import sys

# Check environment variables
env_vars = ['MONGODB_URL', 'REDIS_URL', 'ENVIRONMENT']
missing = []

for var in env_vars:
    if var in os.environ:
        print(f'✅ {var} = {os.environ[var]}')
    else:
        print(f'❌ {var} not set')
        missing.append(var)

if missing:
    print(f'\\n❌ Missing environment variables: {missing}')
    sys.exit(1)
else:
    print('\\n✅ All required environment variables are set')
"

echo -e "\n✅ Test setup validation complete!"