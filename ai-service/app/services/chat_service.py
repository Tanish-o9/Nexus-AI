from __future__ import annotations

import json
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse, Citation, StreamChunk
from app.prompts.templates import get_prompt
from app.services.llm import get_streaming_llm, get_sync_llm
from app.agents import emaos_graph, EMaosState

CITATION_DELIMITER = '__CITATIONS__'


# ── History conversion ────────────────────────────────────────────────────────

def _build_history(request: ChatRequest) -> list:
    """Convert ChatMessage list → LangChain message objects."""
    lc_messages = []
    for msg in request.history:
        if msg.role == 'user':
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == 'assistant':
            lc_messages.append(AIMessage(content=msg.content))
        elif msg.role == 'system':
            lc_messages.append(SystemMessage(content=msg.content))
    return lc_messages


# ── Citation parsing ──────────────────────────────────────────────────────────

def _parse_citations(raw: str) -> tuple[str, list[Citation]]:
    """
    Split raw LLM output into (content, citations).
    The LLM appends: __CITATIONS__[{"id":...}, ...]
    """
    idx = raw.find(CITATION_DELIMITER)
    if idx == -1:
        return raw, []
    content = raw[:idx].rstrip()
    try:
        citations_data = json.loads(raw[idx + len(CITATION_DELIMITER):])
        citations = [Citation(**c) for c in citations_data]
    except (json.JSONDecodeError, TypeError):
        citations = []
    return content, citations


# ── Retry wrapper ─────────────────────────────────────────────────────────────

def _is_retryable(exc: Exception) -> bool:
    """Retry on OpenAI rate limit (429) and server errors (500/503)."""
    msg = str(exc).lower()
    return any(code in msg for code in ('429', '500', '503', 'rate limit', 'timeout'))


# ── Core streaming pipeline ───────────────────────────────────────────────────

async def stream_chat(request: ChatRequest) -> AsyncIterator[str]:
    """
    Yields raw token strings one at a time.
    The router wraps each in `data: <token>\\n\\n` SSE format.

    Citation handling:
    - Tokens are buffered to detect the __CITATIONS__ delimiter
    - Once [DONE], citations are parsed and yielded as a special JSON event
    """
    settings = get_settings()
    prompt = get_prompt('chat_v1')
    llm = get_streaming_llm()
    chain = prompt | llm

    history = _build_history(request)
    buffer = ''

    try:
        async for chunk in chain.astream({
            'message': request.message,
            'history': history,
            'org_id': request.org_id or 'N/A',
            'project_id': request.project_id or 'N/A',
        }):
            token = chunk.content if hasattr(chunk, 'content') else str(chunk)
            buffer += token

            # Don't stream the citation block — hold it back
            if CITATION_DELIMITER in buffer:
                # Yield everything before the delimiter, then stop streaming tokens
                pre, _ = buffer.split(CITATION_DELIMITER, 1)
                if pre:
                    yield pre
                break

            yield token

    except Exception as exc:
        if _is_retryable(exc):
            # Surface retryable errors as a special token so the client knows
            yield f'\n\n[Retrying due to: {type(exc).__name__}]'
        raise

    # Parse and yield citations as a structured JSON event
    content, citations = _parse_citations(buffer)
    if citations:
        citations_payload = json.dumps([c.model_dump() for c in citations])
        yield f'{CITATION_DELIMITER}{citations_payload}'


# ── Non-streaming collect ─────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Collects the full streaming response into a ChatResponse.
    Retried up to 3 times with exponential backoff on transient errors.
    """
    settings = get_settings()
    prompt = get_prompt('chat_v1')
    llm = get_sync_llm()
    chain = prompt | llm

    history = _build_history(request)

    result = await chain.ainvoke({
        'message': request.message,
        'history': history,
        'org_id': request.org_id or 'N/A',
        'project_id': request.project_id or 'N/A',
    })

    raw = result.content if hasattr(result, 'content') else str(result)
    content, citations = _parse_citations(raw)

    return ChatResponse(
        session_id=request.session_id,
        content=content,
        citations=citations,
        agent_trace=['chat_v1'],
    )


# ── EMAOS multi-agent invocation ──────────────────────────────────────────────

async def agent_chat(request: ChatRequest) -> ChatResponse:
    """
    Runs the full EMAOS LangGraph pipeline:
    planner → executor → reviewer → memory_writer
    Returns the assembled final response.
    """
    initial_state: EMaosState = {
        'user_message': request.message,
        'session_id': request.session_id,
        'user_id': request.user_id,
        'org_id': request.org_id,
        'project_id': request.project_id,
        'subtasks': [],
        'current_subtask_index': 0,
        'executor_output': '',
        'tool_trace': [],
        'review_decision': '',
        'review_feedback': '',
        'retry_count': 0,
        'completed_outputs': [],
        'memory_summary': '',
        'final_response': '',
    }

    final_state = await emaos_graph.ainvoke(initial_state)

    content, citations = _parse_citations(final_state.get('final_response', ''))

    return ChatResponse(
        session_id=request.session_id,
        content=content,
        citations=citations,
        agent_trace=final_state.get('subtasks', []),
    )
