import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import stream_chat, chat, agent_chat, CITATION_DELIMITER
from app.dependencies import verify_internal_secret

router = APIRouter(prefix='/api/chat', tags=['chat'])


@router.post(
    '/stream',
    dependencies=[Depends(verify_internal_secret)],
    summary='Stream a chat response token by token (SSE)',
)
async def chat_stream(request: ChatRequest, http_request: Request):
    """
    SSE stream format:
      Regular token  → data: <token>\\n\\n
      Citations      → data: __CITATIONS__[{...}]\\n\\n
      Done           → data: [DONE]\\n\\n
      Error          → data: [ERROR] <message>\\n\\n
    """
    async def event_generator():
        try:
            async for chunk in stream_chat(request):
                # Check if client disconnected — stop generating
                if await http_request.is_disconnected():
                    break

                if chunk.startswith(CITATION_DELIMITER):
                    # Citation block — send as its own event so frontend can parse
                    yield f'data: {chunk}\n\n'
                else:
                    yield f'data: {chunk}\n\n'

            yield 'data: [DONE]\n\n'

        except asyncio.CancelledError:
            # Client navigated away — clean exit, no error
            yield 'data: [DONE]\n\n'
        except Exception as e:
            yield f'data: [ERROR] {str(e)}\n\n'
            yield 'data: [DONE]\n\n'

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@router.post(
    '/agent',
    response_model=ChatResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary='Full EMAOS multi-agent pipeline (non-streaming)',
)
async def chat_agent(request: ChatRequest):
    """
    Runs the full planner → executor → reviewer → memory_writer graph.
    Use for complex multi-step tasks. Slower than /stream but more thorough.
    """
    try:
        return await agent_chat(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    '/',
    response_model=ChatResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary='Non-streaming chat — returns full response',
)
async def chat_sync(request: ChatRequest):
    try:
        return await chat(request)
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail='Chat pipeline not yet implemented.',
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
