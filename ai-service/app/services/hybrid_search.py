"""
Hybrid Search Service
=====================
Combines vector similarity (pgvector) + full-text search (PostgreSQL tsvector)
with weighted score fusion.

Why hybrid?
  - Vector search is great for semantic similarity ("find docs about budget planning")
  - Full-text search is great for exact keyword matching ("Q3 2024 revenue")
  - Combining both gives better results than either alone

How fusion works:
  - Vector score: 1.0 - cosine_distance (already 0 to 1)
  - Keyword score: ts_rank(cd, query) / ts_rank(cd, query) max → normalized 0 to 1
  - Final score = (0.7 * vector_score) + (0.3 * keyword_score)

  The weights (0.7 / 0.3) favour semantic matching but still boost exact
  keyword hits. These are configurable per-request.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import DocumentChunkModel
from app.schemas.documents import HybridSearchResult
from app.services.embeddings import embed_text


# Default fusion weights — semantic > keyword, but keyword still matters
ALPHA_DEFAULT = 0.7  # vector weight
BETA_DEFAULT = 0.3   # keyword weight


async def hybrid_search_chunks(
    session: AsyncSession,
    *,
    query: str,
    org_id: str,
    project_id: Optional[str] = None,
    top_k: int = 5,
    alpha: float = ALPHA_DEFAULT,
    beta: float = BETA_DEFAULT,
) -> List[HybridSearchResult]:
    """
    Run vector + keyword search and return fused results.

    Steps:
      1. Generate embedding for the query (same model used at ingestion)
      2. Run vector search using pgvector cosine distance
      3. Run keyword search using PostgreSQL full-text search
      4. Fuse scores from both and return top_k results

    Args:
        session: DB session
        query: The search text (embedded for vector, parsed for full-text)
        org_id: Organisation ID for data isolation
        project_id: Optional project ID for further scoping
        top_k: How many results to return
        alpha: Weight for vector score (default 0.7)
        beta: Weight for keyword score (default 0.3)
    """
    # Step 1: get the query embedding
    query_embedding = await embed_text(query)

    # Step 2: build the SQL filter for org/project isolation
    filters = [DocumentChunkModel.embedding.isnot(None)]
    filters.append(DocumentChunkModel.metadata_['org_id'].astext == org_id)
    if project_id is not None:
        filters.append(
            DocumentChunkModel.metadata_['project_id'].astext == project_id
        )

    # Step 3: Run vector search
    # Cosine distance → similarity score (1.0 - distance)
    distance_col = DocumentChunkModel.embedding.cosine_distance(query_embedding)
    vec_score = (1.0 - distance_col).label('vec_score')

    # Step 4: Run keyword search using PostgreSQL's built-in full-text search
    #   - plainto_tsquery('english', query) converts the query to tsquery terms
    #   - to_tsvector('english', content) indexes words in the chunk content
    #   - ts_rank gives a relevance score based on term frequency / position
    keyword_query = func.plainto_tsquery('english', query)
    content_vector = func.to_tsvector('english', DocumentChunkModel.content)
    kw_score = func.ts_rank(content_vector, keyword_query).label('kw_score')

    # Step 5: Combine both in one query using COALESCE (keyword score is NULL
    # if no match found)
    fused = func.coalesce(alpha * vec_score, 0.0) + func.coalesce(beta * kw_score, 0.0)
    fused = fused.label('score')

    stmt = (
        select(
            DocumentChunkModel,
            vec_score,
            kw_score,
            fused,
        )
        .where(*filters)
        # At least one of the scores must be > 0 to appear
        .where(
            (vec_score > 0) | (kw_score > 0)
        )
        .order_by(fused.desc())
        .limit(top_k)
    )

    rows = (await session.execute(stmt)).all()

    results: List[HybridSearchResult] = []
    for chunk, vec_s, kw_s, final_score in rows:
        vec_s = float(vec_s) if vec_s is not None else 0.0
        kw_s = float(kw_s) if kw_s is not None else 0.0
        results.append(
            HybridSearchResult(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                score=round(float(final_score), 4),
                vector_score=round(vec_s, 4),
                keyword_score=round(kw_s, 4),
                metadata=chunk.metadata_,
            )
        )
    return results


async def create_fts_index(session: AsyncSession) -> None:
    """
    Create a GIN index for full-text search on content column.
    This makes ts_rank queries much faster on large datasets.

    Idempotent — safe to run on every restart.
    """
    index_name = 'ix_document_chunks_content_gin'
    ddl = text(f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON ai_document_chunks
        USING GIN (to_tsvector('english', content));
    """)
    await session.execute(ddl)
    await session.commit()