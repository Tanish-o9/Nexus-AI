"""
Tests for the embedding service (SentenceTransformers wrapper).
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import numpy as np


# ── embed_text ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_embed_text_returns_list_of_floats():
    """embed_text should return a normalized list of floats."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])

    with patch('app.services.embeddings._get_model', return_value=mock_model):
        from app.services.embeddings import embed_text
        result = await embed_text('hello world')

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(v, float) for v in result)
    mock_model.encode.assert_called_once_with(
        'hello world', normalize_embeddings=True
    )


@pytest.mark.asyncio
async def test_embed_text_runs_in_executor():
    """Verify the synchronous model call is offloaded to a thread pool."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.42] * 384)

    with patch('app.services.embeddings._get_model', return_value=mock_model), \
         patch('asyncio.get_running_loop') as mock_loop:

        mock_loop.return_value.run_in_executor = AsyncMock(
            return_value=[0.42] * 384
        )
        from app.services.embeddings import embed_text
        result = await embed_text('test')

    mock_loop.return_value.run_in_executor.assert_called_once()


# ── embed_texts (batch) ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_embed_texts_returns_list_of_lists():
    """Batch embedding should return one embedding per input string."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])

    with patch('app.services.embeddings._get_model', return_value=mock_model):
        from app.services.embeddings import embed_texts
        results = await embed_texts(['text a', 'text b'])

    assert len(results) == 2
    assert all(isinstance(v, list) for v in results)
    assert all(isinstance(x, float) for v in results for x in v)


@pytest.mark.asyncio
async def test_embed_texts_empty():
    """An empty input list should return an empty list without calling
    the model."""
    with patch('app.services.embeddings._get_model') as mock_model_fn:
        from app.services.embeddings import embed_texts
        results = await embed_texts([])

    assert results == []
    mock_model_fn.return_value.encode.assert_not_called()


# ── Model caching ──────────────────────────────────────────────────────────────
# Note: `lru_cache` on `_get_model` is stdlib behaviour tested by CPython
# itself.  We don't replicate that here to avoid loading the heavy
# SentenceTransformers model.
