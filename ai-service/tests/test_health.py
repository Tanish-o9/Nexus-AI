import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import get_settings


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as c:
        yield c


@pytest.fixture
def secret():
    return get_settings().INTERNAL_SERVICE_SECRET


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_liveness(client):
    res = await client.get('/health/live')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'


@pytest.mark.asyncio
async def test_readiness(client):
    res = await client.get('/health/ready')
    assert res.status_code == 200
    data = res.json()
    assert 'status' in data
    assert 'checks' in data


# ── Internal secret enforcement ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_stream_requires_secret(client):
    res = await client.post('/api/chat/stream', json={
        'message': 'hello',
        'session_id': 'test-session',
        'user_id': 'test-user',
    })
    assert res.status_code == 422  # Missing header → validation error


@pytest.mark.asyncio
async def test_chat_stream_wrong_secret_rejected(client):
    res = await client.post(
        '/api/chat/stream',
        json={
            'message': 'hello',
            'session_id': 'test-session',
            'user_id': 'test-user',
        },
        headers={'X-Internal-Secret': 'wrong-secret'},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_chat_stream_valid_secret_accepted(client, secret):
    """
    With a valid secret the endpoint is reachable.
    Returns stub response since chat_service is not yet implemented.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as c:
        async with c.stream(
            'POST',
            '/api/chat/stream',
            json={
                'message': 'hello',
                'session_id': 'sess-1',
                'user_id': 'user-1',
            },
            headers={'X-Internal-Secret': secret},
        ) as res:
            assert res.status_code == 200
            assert res.headers['content-type'].startswith('text/event-stream')
            body = await res.aread()
            assert b'data:' in body


@pytest.mark.asyncio
async def test_chat_sync_not_implemented(client, secret):
    from unittest.mock import patch, AsyncMock
    with patch('app.routers.chat.chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = NotImplementedError("Chat sync not implemented")
        res = await client.post(
            '/api/chat/',
            json={
                'message': 'hello',
                'session_id': 'sess-2',
                'user_id': 'user-2',
            },
            headers={'X-Internal-Secret': secret},
        )
        assert res.status_code == 501


# ── Prompt registry ───────────────────────────────────────────────────────────

def test_prompt_registry_has_all_agents():
    from app.prompts.templates import PROMPT_REGISTRY
    required = {'chat_v1', 'planner_v1', 'executor_v1', 'reviewer_v1', 'memory_writer_v1'}
    assert required.issubset(set(PROMPT_REGISTRY.keys()))


def test_get_prompt_raises_on_unknown():
    from app.prompts.templates import get_prompt
    with pytest.raises(KeyError):
        get_prompt('nonexistent_v99')


# ── Config ────────────────────────────────────────────────────────────────────

def test_settings_are_cached():
    from app.config import get_settings
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2  # lru_cache — same object
