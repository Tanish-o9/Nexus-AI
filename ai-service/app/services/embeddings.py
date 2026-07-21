"""
Embedding Service
=================
Lazy-loads a SentenceTransformers model once (module-level singleton) and
provides a simple async wrapper so the rest of the service never blocks on
inference.

Why SentenceTransformers over OpenAI embeddings:
  - No per-request API cost at scale.
  - Works offline / air-gapped.
  - all-MiniLM-L6-v2 is 384 dims → fast HNSW search, small index.
  - Easy to swap for a larger model (e.g. BAAI/bge-large-en-v1.5) later.

Why lazy-loading:
  - The model is ~80 MB on disk. Loading it at import time would slow
    down every worker start. We load once on first use.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import List

from app.config import get_settings

# ---------------------------------------------------------------------------
# Synchronous model singleton (thread-safe via LRU cache)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_model():
    """Return the cached SentenceTransformer model instance.

    Cached by ``lru_cache(maxsize=1)`` so the model is loaded exactly once
    per process.  The cache key is the model name, so changing
    ``EMBEDDING_MODEL`` in settings will trigger a fresh load.
    """
    from sentence_transformers import SentenceTransformer
    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def embed_text(text: str) -> List[float]:
    """Embed a single text string.

    Runs the synchronous model in a thread-pool executor so the async
    event loop is never blocked.
    """
    model = _get_model()
    loop = asyncio.get_running_loop()
    embedding = await loop.run_in_executor(
        None, lambda: model.encode(text, normalize_embeddings=True).tolist()
    )
    return embedding


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of text strings (much faster than calling
    ``embed_text`` in a loop because SentenceTransformers vectorises
    the batch internally).
    """
    if not texts:
        return []
    model = _get_model()
    loop = asyncio.get_running_loop()
    embeddings = await loop.run_in_executor(
        None,
        lambda: model.encode(texts, normalize_embeddings=True).tolist(),
    )
    return embeddings