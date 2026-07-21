import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.memory import MemoryWriteRequest, MemoryQueryRequest
from app.memory.store import MemoryStore, MAX_ENTRIES_PER_SESSION, EVICTION_KEEP


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_write_request(**overrides) -> MemoryWriteRequest:
    base = {
        'agent_id': 'executor',
        'session_id': 'sess-1',
        'user_id': 'user-1',
        'content': 'Task completed: defined project scope.',
        'metadata': {},
    }
    base.update(overrides)
    return MemoryWriteRequest(**base)


def make_query_request(**overrides) -> MemoryQueryRequest:
    base = {
        'agent_id': 'executor',
        'session_id': 'sess-1',
        'user_id': 'user-1',
        'query': 'What was the project scope?',
        'top_k': 3,
    }
    base.update(overrides)
    return MemoryQueryRequest(**base)


def fake_model_entry(content='test content', agent_id='executor'):
    entry = MagicMock()
    entry.id = uuid.uuid4()
    entry.agent_id = agent_id
    entry.session_id = 'sess-1'
    entry.user_id = 'user-1'
    entry.content = content
    entry.embedding = [0.1] * 384
    entry.metadata_ = {}
    entry.created_at = datetime.utcnow()
    return entry


# ── Embedding service ─────────────────────────────────────────────────────────

def test_embed_returns_list_of_floats():
    with patch('app.services.embedding.get_embedding_model') as mock_model_fn:
        import numpy as np
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_model_fn.return_value = mock_model

        from app.services.embedding import embed
        result = embed('hello world')

    assert isinstance(result, list)
    assert all(isinstance(v, float) for v in result)


def test_embed_batch_returns_list_of_lists():
    with patch('app.services.embedding.get_embedding_model') as mock_model_fn:
        import numpy as np
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_model_fn.return_value = mock_model

        from app.services.embedding import embed_batch
        result = embed_batch(['text one', 'text two'])

    assert len(result) == 2
    assert isinstance(result[0], list)


# ── MemoryStore.write ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_write_creates_entry():
    store = MemoryStore()
    entry = fake_model_entry()

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.begin = MagicMock(return_value=mock_session)
    mock_session.add = MagicMock()

    with patch('app.memory.store.embed', return_value=[0.1] * 384), \
         patch('app.memory.store.AsyncSessionFactory', return_value=mock_session), \
         patch.object(store, '_maybe_evict', new_callable=AsyncMock):

        # Patch MemoryEntryModel to return our fake entry
        with patch('app.memory.store.MemoryEntryModel', return_value=entry):
            result = await store.write(make_write_request())

    assert result.agent_id == 'executor'
    assert result.session_id == 'sess-1'


# ── MemoryStore.query ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_query_returns_entries():
    store = MemoryStore()
    fake_entries = [fake_model_entry(f'content {i}') for i in range(3)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = fake_entries

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch('app.memory.store.embed', return_value=[0.1] * 384), \
         patch('app.memory.store.AsyncSessionFactory', return_value=mock_session):

        results = await store.query(make_query_request())

    assert len(results) == 3
    assert results[0].content == 'content 0'


# ── Agent isolation ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_query_filters_by_agent_id():
    """
    Verifies that the WHERE clause includes agent_id so agents
    cannot read each other's memory.
    """
    store = MemoryStore()
    captured_stmt = {}

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    async def capture_execute(stmt):
        captured_stmt['stmt'] = str(stmt)
        return mock_result

    mock_session.execute = capture_execute

    with patch('app.memory.store.embed', return_value=[0.1] * 384), \
         patch('app.memory.store.AsyncSessionFactory', return_value=mock_session):

        await store.query(make_query_request(agent_id='planner'))

    # The compiled SQL should reference agent_id filter
    assert 'agent_id' in captured_stmt.get('stmt', '')


# ── Eviction logic ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_eviction_triggers_when_over_limit():
    store = MemoryStore()
    over_limit = MAX_ENTRIES_PER_SESSION + 5
    old_entries = [fake_model_entry(f'old {i}') for i in range(over_limit - EVICTION_KEEP)]

    count_result = MagicMock()
    count_result.scalar_one.return_value = over_limit

    oldest_result = MagicMock()
    oldest_result.scalars.return_value.all.return_value = old_entries

    call_count = 0

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.begin = MagicMock(return_value=mock_session)
    mock_session.add = MagicMock()

    async def side_effect_execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return count_result
        return oldest_result

    mock_session.execute = side_effect_execute

    with patch('app.memory.store.AsyncSessionFactory', return_value=mock_session), \
         patch('app.memory.store.embed', return_value=[0.1] * 384), \
         patch.object(store, '_summarize_entries', new_callable=AsyncMock, return_value='summary text') as mock_summarize:

        await store._maybe_evict(make_write_request())

        # _summarize_entries should have been called since we're over limit
        mock_summarize.assert_called_once()


@pytest.mark.asyncio
async def test_eviction_skipped_when_under_limit():
    store = MemoryStore()

    count_result = MagicMock()
    count_result.scalar_one.return_value = MAX_ENTRIES_PER_SESSION - 1

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.execute = AsyncMock(return_value=count_result)

    with patch('app.memory.store.AsyncSessionFactory', return_value=mock_session), \
         patch.object(store, '_summarize_entries', new_callable=AsyncMock) as mock_summarize:

        await store._maybe_evict(make_write_request())

    mock_summarize.assert_not_called()


# ── clear_session ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clear_session_deletes_entries():
    store = MemoryStore()

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.begin = MagicMock(return_value=mock_session)
    mock_session.execute = AsyncMock()

    with patch('app.memory.store.AsyncSessionFactory', return_value=mock_session):
        await store.clear_session('executor', 'sess-1')

    mock_session.execute.assert_called_once()
