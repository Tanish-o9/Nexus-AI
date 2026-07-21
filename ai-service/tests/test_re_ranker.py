"""
Tests for re-ranker and citations services.
"""

import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.schemas.documents import HybridSearchResult


def make_result(content='test content', score=0.5, source='doc.pdf'):
    return HybridSearchResult(
        chunk_id=str(uuid.uuid4()),
        document_id=str(uuid.uuid4()),
        content=content,
        chunk_index=0,
        score=score,
        vector_score=score,
        keyword_score=0.0,
        metadata={'source': source, 'org_id': 'org-1'},
    )


# ─── RE-RANKER TESTS ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rerank_returns_top_k():
    from app.services.re_ranker import rerank
    results = [make_result(content=f'doc {i}', score=0.5) for i in range(10)]
    mock_scores = [float(i) for i in range(10, 0, -1)]

    with patch('app.services.re_ranker._get_cross_encoder') as mock_get:
        mock_model = MagicMock()
        mock_model.predict.return_value = mock_scores
        mock_get.return_value = mock_model
        reranked = await rerank('test query', results, top_k=3)

    assert len(reranked) == 3
    assert reranked[0].score > reranked[1].score


@pytest.mark.asyncio
async def test_rerank_empty_input():
    from app.services.re_ranker import rerank
    result = await rerank('test', [])
    assert result == []


@pytest.mark.asyncio
async def test_rerank_sorts_by_score():
    from app.services.re_ranker import rerank
    results = [make_result(content='a'), make_result(content='b')]

    with patch('app.services.re_ranker._get_cross_encoder') as mock_get:
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.3, 0.9]
        mock_get.return_value = mock_model
        reranked = await rerank('test', results, top_k=5)

    assert len(reranked) == 2
    assert reranked[0].score == 1.0
    assert reranked[1].score == 0.0


# ─── CITATIONS TESTS ───────────────────────────────────────────────────────

def test_results_to_citations_basic():
    from app.services.citations import results_to_citations
    results = [make_result(content='This is about AI and machine learning.', source='report.pdf')]
    citations = results_to_citations(results)

    assert len(citations) == 1
    c = citations[0]
    assert c.id == 'src_1'
    assert c.title == 'report.pdf'
    assert c.source == 'report.pdf'
    assert 'AI and machine learning' in c.excerpt


def test_results_to_citations_truncates_long_content():
    from app.services.citations import results_to_citations
    long_content = 'A' * 500
    results = [make_result(content=long_content)]
    citations = results_to_citations(results)
    assert len(citations[0].excerpt) <= 204


def test_results_to_citations_max_citations():
    from app.services.citations import results_to_citations
    results = [make_result(content=f'doc {i}') for i in range(10)]
    citations = results_to_citations(results, max_citations=3)
    assert len(citations) == 3


def test_format_citations_for_prompt():
    from app.services.citations import format_citations_for_prompt
    results = [
        make_result(content='Budget planning is important.', source='budget.pdf'),
        make_result(content='Team velocity improved.', source='sprint.md'),
    ]
    prompt_text = format_citations_for_prompt(results)
    assert '[Source 1]' in prompt_text
    assert '[Source 2]' in prompt_text
    assert 'Budget planning' in prompt_text
    assert 'Team velocity' in prompt_text