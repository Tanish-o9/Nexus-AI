import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import get_settings
from app.schemas.chat import ChatRequest, ChatMessage
from app.services.chat_service import (
    _build_history, _parse_citations, stream_chat, chat, CITATION_DELIMITER
)


SECRET = get_settings().INTERNAL_SERVICE_SECRET

BASE_REQUEST = {
    'message': 'What is the status of project Alpha?',
    'session_id': 'sess-test-1',
    'user_id': 'user-abc',
    'org_id': 'org-123',
    'project_id': 'proj-456',
    'history': [],
}


# ── _build_history ────────────────────────────────────────────────────────────

def test_build_history_empty():
    req = ChatRequest(**BASE_REQUEST)
    assert _build_history(req) == []


def test_build_history_converts_roles():
    from langchain_core.messages import HumanMessage, AIMessage
    req = ChatRequest(**{
        **BASE_REQUEST,
        'history': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'},
        ],
    })
    history = _build_history(req)
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert history[0].content == 'Hello'


# ── _parse_citations ──────────────────────────────────────────────────────────

def test_parse_citations_no_delimiter():
    content, citations = _parse_citations('Just a plain answer.')
    assert content == 'Just a plain answer.'
    assert citations == []


def test_parse_citations_with_valid_json():
    raw = 'The answer is X.' + CITATION_DELIMITER + json.dumps([
        {'id': '1', 'title': 'Doc A', 'source': 'http://a.com', 'excerpt': 'excerpt A'}
    ])
    content, citations = _parse_citations(raw)
    assert content == 'The answer is X.'
    assert len(citations) == 1
    assert citations[0].title == 'Doc A'


def test_parse_citations_malformed_json():
    raw = 'Answer' + CITATION_DELIMITER + 'not-valid-json'
    content, citations = _parse_citations(raw)
    assert content == 'Answer'
    assert citations == []


# ── stream_chat ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_chat_yields_tokens():
    """Mock the LLM chain to yield fake tokens and verify they stream out."""
    mock_chunks = [
        MagicMock(content='Project '),
        MagicMock(content='Alpha '),
        MagicMock(content='is active.'),
    ]

    async def mock_astream(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    with patch('app.services.chat_service.get_streaming_llm') as mock_llm_fn:
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.astream = mock_astream
        mock_llm_fn.return_value = mock_llm

        with patch('app.services.chat_service.get_prompt') as mock_prompt_fn:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_prompt_fn.return_value = mock_prompt

            req = ChatRequest(**BASE_REQUEST)
            tokens = []
            async for token in stream_chat(req):
                tokens.append(token)

    assert 'Project ' in tokens
    assert 'Alpha ' in tokens
    assert 'is active.' in tokens


@pytest.mark.asyncio
async def test_stream_chat_yields_citations():
    """Citations appended by LLM are parsed and yielded as a special chunk."""
    citation_json = json.dumps([
        {'id': '1', 'title': 'Spec', 'source': 'http://x.com', 'excerpt': 'text'}
    ])
    full_response = f'The answer.' + CITATION_DELIMITER + citation_json

    mock_chunks = [MagicMock(content=full_response)]

    async def mock_astream(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    with patch('app.services.chat_service.get_streaming_llm') as mock_llm_fn:
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.astream = mock_astream
        mock_llm_fn.return_value = mock_llm

        with patch('app.services.chat_service.get_prompt') as mock_prompt_fn:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_prompt_fn.return_value = mock_prompt

            req = ChatRequest(**BASE_REQUEST)
            chunks = []
            async for chunk in stream_chat(req):
                chunks.append(chunk)

    citation_chunk = next((c for c in chunks if CITATION_DELIMITER in c), None)
    assert citation_chunk is not None
    assert 'Spec' in citation_chunk


# ── chat (non-streaming) ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_returns_response():
    mock_result = MagicMock()
    mock_result.content = 'Alpha is active with 3 tasks.'

    with patch('app.services.chat_service.get_sync_llm') as mock_llm_fn:
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_result)
        mock_llm_fn.return_value = mock_llm

        with patch('app.services.chat_service.get_prompt') as mock_prompt_fn:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_prompt_fn.return_value = mock_prompt

            req = ChatRequest(**BASE_REQUEST)
            response = await chat(req)

    assert response.session_id == BASE_REQUEST['session_id']
    assert response.content == 'Alpha is active with 3 tasks.'
    assert response.citations == []
    assert 'chat_v1' in response.agent_trace


# ── SSE endpoint via HTTP ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stream_endpoint_returns_sse():
    mock_chunks = [MagicMock(content='Hello '), MagicMock(content='world')]

    async def mock_astream(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    with patch('app.services.chat_service.get_streaming_llm') as mock_llm_fn:
        mock_llm = MagicMock()
        mock_chain = MagicMock()
        mock_chain.astream = mock_astream
        mock_llm_fn.return_value = mock_llm

        with patch('app.services.chat_service.get_prompt') as mock_prompt_fn:
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_prompt_fn.return_value = mock_prompt

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url='http://test'
            ) as client:
                async with client.stream(
                    'POST',
                    '/api/chat/stream',
                    json=BASE_REQUEST,
                    headers={'X-Internal-Secret': SECRET},
                ) as res:
                    assert res.status_code == 200
                    assert 'text/event-stream' in res.headers['content-type']
                    body = await res.aread()
                    assert b'data:' in body
                    assert b'[DONE]' in body
