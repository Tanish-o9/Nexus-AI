"""
Run this once after the initial table creation to create the HNSW vector index.
SQLAlchemy doesn't support HNSW natively so we create it via raw SQL.

Usage:
    python -m app.memory.migrations
"""
import asyncio
from app.memory.database import engine


HNSW_INDEX_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE INDEX IF NOT EXISTS ix_memory_embedding_hnsw
ON ai_memory_entries
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
"""

# Why HNSW over IVFFlat:
# - HNSW: no training phase, good recall (>95%) at small-medium scale,
#         insert-friendly, works well up to ~1M vectors
# - IVFFlat: requires VACUUM + retraining as data grows,
#            better throughput only at 1M+ vectors
# - m=16: number of connections per node (higher = better recall, more memory)
# - ef_construction=64: build-time search width (higher = better index quality)


async def run():
    async with engine.begin() as conn:
        for statement in HNSW_INDEX_SQL.strip().split(';'):
            stmt = statement.strip()
            if stmt:
                await conn.exec_driver_sql(stmt)
    print('HNSW index created successfully.')


if __name__ == '__main__':
    asyncio.run(run())
