"""
Tests for hybrid search (vector + full-text with score fusion).
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.documents import HybridSearchResult


def make_fake_chunk(content='some content', org_id='org-1', project_id=None, chunk_index=0):
    chunk = MagicMock()
    chunk.id = uuid.uuid4()
    chunk.document_id = uuid.uuid4()
    chunk.content = content
    chunk.chunk_index = chunk_index
    chunk.metadata_ = {
        'source': 'doc.pdf', 'org_id': org_id,
        'project_id': project_id, 'uploaded_by': 'user-1',
    }
    return chunk


@pytest.mark.asyncio
async def test_hybrid_search_returns_results_with_scores():
    """Hybrid search should return results with vec_score, kw_score, and fused score."""
    from app.services.hybrid_search import hybrid_search_chunks

    fake_chunks = [make_fake_chunk(content='budget planning 2024')]
    mock_rows = [(fake_chunks[0], 0.85, 0.4, 0.715)]  # chunk, vec_s, kw_s, fused

    mock_result = MagicMock()
    mock_result.all.return_value = mock_rows

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.services.hybrid_search.embed_text', return_value=[0.1] * 384):
        results = await hybrid_search_chunks(
            mock_session, query='budget', org_id='org-1', top_k=5,
        )

    assert len(results) == 1
    r = results[0]
    assert isinstance(r, HybridSearchResult)
    assert r.vector_score == 0.85
    assert r.keyword_score == 0.4
    assert r.score == 0.715  # 0.7*0.85 + 0.3*0.4 = 0.595 + 0.12 = 0.715


@pytest.mark.asyncio
async def test_hybrid_search_filters_by_org():
    """SQL must filter by org_id via metadata ->>."""
    from app.services.hybrid_search import hybrid_search_chunks

    captured = {}

    async def capture_execute(stmt):
        captured['sql'] = str(stmt)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        return mock_result

    mock_session = AsyncMock()
    mock_session.execute = capture_execute

    with patch('app.services.hybrid_search.embed_text', return_value=[0.1] * 384):
        await hybrid_search_chunks(mock_session, query='test', org_id='org-99')

    sql = captured.get('sql', '')
    assert "metadata ->>" in sql


@pytest.mark.asyncio
async def test_hybrid_search_with_project_id():
    """When project_id given, SQL must have two metadata filters + AND."""
    from app.services.hybrid_search import hybrid_search_chunks

    captured = {}

    async def capture_execute(stmt):
        captured['sql'] = str(stmt)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        return mock_result

    mock_session = AsyncMock()
    mock_session.execute = capture_execute

    with patch('app.services.hybrid_search.embed_text', return_value=[0.1] * 384):
        await hybrid_search_chunks(
            mock_session, query='test', org_id='org-1', project_id='proj-5'
        )

    sql = captured.get('sql', '')
    assert sql.count("metadata ->>") >= 2


@pytest.mark.asyncio
async def test_hybrid_search_custom_weights():
    """Custom alpha/beta should be passed through to the fused score.

    NOTE: The fused score comes from the DB query (SQL does the computation),
    so in this mock test we verify the values are passed through correctly
    by providing a pre-computed fused score.
    """
    from app.services.hybrid_search import hybrid_search_chunks

    fake_chunks = [make_fake_chunk(content='hello world')]
    # The DB returns (chunk, vec_score, kw_score, fused_score)
    # With alpha=0.5, beta=0.5: 0.5*0.8 + 0.5*0.5 = 0.65
    mock_rows = [(fake_chunks[0], 0.8, 0.5, 0.65)]

    mock_result = MagicMock()
    mock_result.all.return_value = mock_rows

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.services.hybrid_search.embed_text', return_value=[0.1] * 384):
        results = await hybrid_search_chunks(
            mock_session, query='hello', org_id='org-1',
            alpha=0.5, beta=0.5,
        )

    assert len(results) == 1
    # The vector_score and keyword_score should be passed through as-is
    assert results[0].vector_score == 0.8
    assert results[0].keyword_score == 0.5
    # The fused score comes from the DB computation
    assert results[0].score == 0.65


@pytest.mark.asyncio
async def test_hybrid_search_empty_result():
    """No matches should return empty list."""
    from app.services.hybrid_search import hybrid_search_chunks

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.services.hybrid_search.embed_text', return_value=[0.1] * 384):
        results = await hybrid_search_chunks(
            mock_session, query='nothing', org_id='org-1'
        )

    assert results == []


@pytest.mark.asyncio
async def test_create_fts_index_executes_ddl():
    """create_fts_index should create GIN index with to_tsvector."""
    from app.services.hybrid_search import create_fts_index

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    await create_fts_index(mock_session)

    mock_session.execute.assert_called_once()
    sql = str(mock_session.execute.call_args[0][0])
    assert 'CREATE INDEX IF NOT EXISTS' in sql
    assert 'ix_document_chunks_content_gin' in sql
    assert 'USING GIN' in sql
    assert "to_tsvector('english', content)" in sql
    mock_session.commit.assert_called_once()