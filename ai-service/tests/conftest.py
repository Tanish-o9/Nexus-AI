"""
Global test configuration for the ai-service.

Force-sets required environment variables before any test module is imported,
so that ``Settings()`` never fails due to missing or invalid env vars.
"""

import os

# Force-set (not setdefault) because the system environment may already have
# DEBUG=release which is not a valid boolean for pydantic.
os.environ['DEBUG'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-key-not-real'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost:5432/test'
os.environ['INTERNAL_SERVICE_SECRET'] = 'test-secret'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
os.environ['EMBEDDING_DIMENSION'] = '384'