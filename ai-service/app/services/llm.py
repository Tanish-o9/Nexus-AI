from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.config import get_settings


@lru_cache(maxsize=1)
def get_llm(streaming: bool = True) -> ChatOpenAI:
    """
    Returns a cached ChatOpenAI instance.
    streaming=True  → used by chat pipeline (token-by-token SSE)
    streaming=False → used by agents that need the full response at once
    """
    settings = get_settings()
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
        streaming=streaming,
    )


def get_streaming_llm() -> ChatOpenAI:
    return get_llm(streaming=True)


def get_sync_llm() -> ChatOpenAI:
    return get_llm(streaming=False)
