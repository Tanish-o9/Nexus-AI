"""
Vector Store Service
====================
pgvector-backed vector store for document chunks with org/project-level
isolation enforced at query time.

Why a dedicated service instead of inline SQL:
  - Keeps the search logic testable without spinning up the full app.
  - Centralises embedding generation + query construction so every caller
    gets consistent isolation and scoring.

Index strategy (HNSW):
  - HNSW is the default choice for this project because:
    1. Build time is slower than IVFFlat, but query latency is far more
       consistent — important for real-time AI chat.
    2. Recall is higher at any given query time budget.
    3. The index is built once at migration time and updated incrementally
       as new chunks are inserted (pgvector handles this).
  - IVFFlat would be a valid alternative if we had >10M rows and could
    tolerate lower recall, but we don't expect that scale at launch.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.memory.models import DocumentChunkModel
from app.schemas.documents import SearchResult
from app.services.embeddings import embed_text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def search_chunks(
    session: AsyncSession,
    *,
    query: str,
    org_id: str,
    project_id: Optional[str] = None,
    top_k: int = 5,
    min_score: float = 0.5,
) -> List[SearchResult]:
    """Hybrid search over document chunks.

    Uses cosine distance on pgvector embeddings.  The query is embedded
    with the same SentenceTransformers model used at ingestion time.

    Isolation:
      - ``org_id`` is **required** — a caller must always scope to an org.
      - ``project_id`` is optional.  If provided, results are further
        scoped to that project.  If omitted, results span the whole org.

    Returns results sorted by similarity (highest first) with a cosine
    similarity score in [0, 1].
    """
    settings = get_settings()
    query_embedding = await embed_text(query)

    # Build the filter clause dynamically so we can handle the optional
    # project_id without string concatenation.
    filters = [DocumentChunkModel.embedding.isnot(None)]
    filters.append(DocumentChunkModel.metadata_['org_id'].astext == org_id)
    if project_id is not None:
        filters.append(
            DocumentChunkModel.metadata_['project_id'].astext == project_id
        )

    # Cosine distance via pgvector's ``<=>`` operator.
    # We cast the Python list to a pgvector literal so SQLAlchemy doesn't
    # try to bind it as a parameter (which would fail type inference).
    distance_col = DocumentChunkModel.embedding.cosine_distance(query_embedding)

    stmt = (
        select(
            DocumentChunkModel,
            distance_col.label('distance'),
        )
        .where(*filters)
        .order_by(distance_col)
        .limit(top_k)
    )

    rows = (await session.execute(stmt)).all()

    results: List[SearchResult] = []
    for chunk, distance in rows:
        # Cosine distance → cosine similarity
        score = 1.0 - float(distance)
        if score < min_score:
            continue
        results.append(
            SearchResult(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                score=round(score, 4),
                metadata=chunk.metadata_,
            )
        )
    return results


async def create_hnsw_index(session: AsyncSession) -> None:
    """Create the HNSW vector index on ``ai_document_chunks.embedding``.

    This is called once at application startup (see ``main.py`` lifespan).
    ``IF NOT EXISTS`` makes it idempotent — safe to run on every restart.

    The index uses:
      - ``vector_cosine_ops`` because we query with ``<=>`` (cosine distance).
      - ``m = 16`` (default) — good balance of recall vs build time.
      - ``ef_construction = 64`` (default) — sufficient for our scale.
    """
    settings = get_settings()
    index_name = 'ix_document_chunks_embedding_hnsw'
    ddl = text(f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON ai_document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    await session.execute(ddl)
    await session.commit()