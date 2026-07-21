"""
Re-ranker Service
=================
Takes top-k results from hybrid search and re-scores them using a
cross-encoder model. This is a "second pass" that improves precision.

Why re-rank?
  - First pass (hybrid search) is fast but may return some irrelevant chunks
  - Cross-encoder scores query + chunk TOGETHER, giving much better relevance
  - Only re-rank top 20-30 results (not all chunks) to keep it fast

How it works:
  1. First pass: hybrid search returns top N results (e.g. 20)
  2. Second pass: cross-encoder re-scores those 20 results
  3. Final: return top K (e.g. 5) from the re-ranked list

Cross-encoder vs Bi-encoder:
  - Bi-encoder (sentence-transformers): fast, good for first pass
  - Cross-encoder: slow but accurate, good for re-ranking top results

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
  - Small, fast enough for re-ranking
  - Trained on MS MARCO (search relevance)
  - Returns score 0 to 1 (higher = more relevant)
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import List, Optional

from app.schemas.documents import HybridSearchResult


@lru_cache(maxsize=1)
def _get_cross_encoder():
    """Load cross-encoder model once and cache it."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


async def rerank(
    query: str,
    results: List[HybridSearchResult],
    top_k: int = 5,
) -> List[HybridSearchResult]:
    """
    Re-rank hybrid search results using a cross-encoder.

    Args:
        query: The original search query
        results: Results from hybrid_search_chunks (or similar)
        top_k: How many results to return after re-ranking

    Returns:
        Re-ranked results with updated scores (0 to 1)
    """
    if not results:
        return []

    # Prepare pairs: (query, chunk_content) for cross-encoder
    pairs = [(query, r.content) for r in results]

    model = _get_cross_encoder()
    loop = asyncio.get_running_loop()

    # Run cross-encoder in thread pool (it's synchronous)
    cross_scores = await loop.run_in_executor(
        None, lambda: model.predict(pairs)
    )
    # Convert to list if numpy array, keep as-is if already list
    if hasattr(cross_scores, 'tolist'):
        cross_scores = cross_scores.tolist()

    # Normalize scores to 0-1 using min-max scaling
    if cross_scores:
        min_s = min(cross_scores)
        max_s = max(cross_scores)
        if max_s > min_s:
            cross_scores = [
                (s - min_s) / (max_s - min_s) for s in cross_scores
            ]
        else:
            cross_scores = [0.5] * len(cross_scores)

    # Update results with cross-encoder scores and sort
    reranked = []
    for result, score in zip(results, cross_scores):
        result.score = round(float(score), 4)
        result.vector_score = round(float(score), 4)  # overwrite with better score
        reranked.append(result)

    # Sort by score descending and take top_k
    reranked.sort(key=lambda r: r.score, reverse=True)
    return reranked[:top_k]