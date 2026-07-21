"""
Citations Service
=================
Turns search results into Citation objects that the chat system can use.
Also attaches citation metadata so the AI knows which sources it used.

The flow is:
  1. User asks a question in chat
  2. We run hybrid search → re-ranker to find relevant chunks
  3. We convert those chunks to Citation objects
  4. Citations are attached to the AI response (visible in the UI)
"""

from typing import List
from app.schemas.chat import Citation
from app.schemas.documents import HybridSearchResult


def results_to_citations(
    results: List[HybridSearchResult],
    max_citations: int = 5,
) -> List[Citation]:
    """
    Convert search results to Citation objects for the chat response.

    Args:
        results: Re-ranked search results
        max_citations: Max citations to include

    Returns:
        List of Citations (id, title, source, excerpt)
    """
    citations = []
    for i, r in enumerate(results[:max_citations]):
        # Get source filename from metadata, fallback to unknown
        source = r.metadata.get('source', 'unknown')
        # Truncate content to excerpt length (200 chars)
        excerpt = r.content[:200]
        if len(r.content) > 200:
            excerpt += '...'

        citations.append(Citation(
            id=f"src_{i + 1}",
            title=source,
            source=source,
            excerpt=excerpt,
        ))
    return citations


def format_citations_for_prompt(
    results: List[HybridSearchResult],
) -> str:
    """
    Format search results as context text that can be injected into
    an AI prompt. Each result includes source + content.

    This is what gives the AI "grounding" — it knows exactly which
    documents it should base its answer on.
    """
    parts = []
    for i, r in enumerate(results):
        parts.append(
            f"[Source {i + 1}]: {r.metadata.get('source', 'unknown')}\n"
            f"Content: {r.content}\n"
        )
    return "\n---\n".join(parts)