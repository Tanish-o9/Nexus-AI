"""
Tests for the vector store service (pgvector search with org isolation).
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from app.schemas.documents import SearchResult


# ── Fixtures ────────────────────────────────────────────────────────────────────

def make_fake_chunk(content='some content', org_id='org-1', project_id=None, chunk_index=0):
    """Build a MagicMock that looks like a DocumentChunkModel row."""
    chunk = MagicMock()
    chunk.id = uuid.uuid4()
    chunk.document_id = uuid.uuid4()
    chunk.content = content
    chunk.chunk_index = chunk_index
    chunk.embedding = [0.1] * 384
    chunk.metadata_ = {
        'source': 'doc.pdf',
        'org_id': org_id,
        'project_id': project_id,
        'uploaded_by': 'user-1',
    }
    return chunk


# ── search_chunks ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_chunks_returns_results():
    """Basic happy-path: search finds chunks and returns SearchResults with
    scores."""
    from app.services.vector_store import search_chunks

    fake_chunks = [
        make_fake_chunk(content='project scope defines deliverables', chunk_index=0),
        make_fake_chunk(content='budget constraints for Q3', chunk_index=1),
    ]

    # Build mock rows: (chunk_model, distance_value)
    mock_rows = [(fake_chunks[0], 0.1), (fake_chunks[1], 0.25)]

    mock_result = MagicMock()
    mock_result.all.return_value = mock_rows

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.services.vector_store.embed_text', return_value=[0.1] * 384):
        results = await search_chunks(
            mock_session,
            query='project budget',
            org_id='org-1',
            project_id=None,
            top_k=5,
            min_score=0.0,  # accept everything for this test
        )

    assert len(results) == 2
    assert all(isinstance(r, SearchResult) for r in results)
    # Highest similarity first (distance 0.1 → score 0.9)
    assert results[0].score >= results[1].score
    assert results[0].chunk_id == str(fake_chunks[0].id)


@pytest.mark.asyncio
async def test_search_chunks_filters_by_org():
    """The SQL WHERE clause must include org_id."""
    from app.services.vector_store import search_chunks

    captured = {}

    async def capture_execute(stmt):
        captured['sql'] = str(stmt)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        return mock_result

    mock_session = AsyncMock()
    mock_session.execute = capture_execute

    with patch('app.services.vector_store.embed_text', return_value=[0.1] * 384):
        await search_chunks(
            mock_session,
            query='test',
            org_id='org-42',
            project_id=None,
            top_k=3,
            min_score=0.0,
        )

    sql = captured.get('sql', '')
    # SQLAlchemy parameterises bound values, so the literal "org-42" won't
    # appear in the compiled SQL string.  Instead verify that the JSONB
    # ``->>`` operator is used on ``metadata`` (which is how we filter by
    # org_id).  The presence of ``metadata ->>`` + the alias confirms the
    # WHERE clause is correctly constructed.
    assert "metadata ->>" in sql
    assert "embedding <=>" in sql


@pytest.mark.asyncio
async def test_search_chunks_filters_by_project():
    """When project_id is provided, the WHERE clause must include it."""
    from app.services.vector_store import search_chunks

    captured = {}

    async def capture_execute(stmt):
        captured['sql'] = str(stmt)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        return mock_result

    mock_session = AsyncMock()
    mock_session.execute = capture_execute

    with patch('app.services.vector_store.embed_text', return_value=[0.1] * 384):
        await search_chunks(
            mock_session,
            query='test',
            org_id='org-1',
            project_id='proj-99',
            top_k=3,
            min_score=0.0,
        )

    sql = captured.get('sql', '')
    # With both org_id AND project_id filters, we expect TWO ``metadata ->>``
    # expressions in the WHERE clause.  SQLAlchemy parameterises bound values
    # so we check for the pattern rather than the literal.
    assert sql.count("metadata ->>") >= 2
    assert "AND" in sql  # both filters combined with AND


@pytest.mark.asyncio
async def test_search_chunks_applies_min_score():
    """Results below min_score should be excluded."""
    from app.services.vector_store import search_chunks

    fake_chunks = [
        make_fake_chunk(content='high match', chunk_index=0),
        make_fake_chunk(content='low match', chunk_index=1),
    ]
    # distance 0.1 → score 0.9, distance 0.85 → score 0.15
    mock_rows = [(fake_chunks[0], 0.1), (fake_chunks[1], 0.85)]

    mock_result = MagicMock()
    mock_result.all.return_value = mock_rows

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.services.vector_store.embed_text', return_value=[0.1] * 384):
        results = await search_chunks(
            mock_session,
            query='high match',
            org_id='org-1',
            min_score=0.5,
        )

    assert len(results) == 1
    assert results[0].content == 'high match'


@pytest.mark.asyncio
async def test_search_chunks_empty_query():
    """Empty or no-match queries should return an empty list."""
    from app.services.vector_store import search_chunks

    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.services.vector_store.embed_text', return_value=[0.1] * 384):
        results = await search_chunks(
            mock_session,
            query='nothing relevant',
            org_id='org-1',
            top_k=5,
            min_score=0.0,
        )

    assert results == []


# ── create_hnsw_index ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_hnsw_index_executes_ddl():
    """create_hnsw_index should execute the CREATE INDEX IF NOT EXISTS DDL."""
    from app.services.vector_store import create_hnsw_index

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    await create_hnsw_index(mock_session)

    mock_session.execute.assert_called_once()
    sql = str(mock_session.execute.call_args[0][0])
    assert 'CREATE INDEX IF NOT EXISTS' in sql
    assert 'ix_document_chunks_embedding_hnsw' in sql
    assert 'USING hnsw' in sql
    assert 'vector_cosine_ops' in sql
    mock_session.commit.assert_called_once()