from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import AsyncSessionFactory, get_session
from app.schemas.documents import (
    DocumentIngestResponse,
    SearchRequest,
    SearchResponse,
    HybridSearchRequest,
    HybridSearchResponse,
)
from app.services.documents import ingest_document
from app.services.vector_store import search_chunks
from app.services.hybrid_search import hybrid_search_chunks

router = APIRouter(prefix='/api/documents', tags=['documents'])


@router.post('/ingest', response_model=DocumentIngestResponse, dependencies=[Depends(verify_internal_secret)], status_code=status.HTTP_201_CREATED)
async def ingest(file: UploadFile = File(...), org_id: str = Form(...), user_id: str = Form(...), project_id: str | None = Form(None)):
    try:
        content = await file.read()
        async with AsyncSessionFactory() as session:
            async with session.begin():
                document, chunk_count = await ingest_document(session, filename=file.filename or 'upload', mime_type=file.content_type or '', content=content, org_id=org_id, project_id=project_id, user_id=user_id)
        return DocumentIngestResponse(document_id=str(document.id), chunk_count=chunk_count, filename=document.filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post('/search', response_model=SearchResponse, dependencies=[Depends(verify_internal_secret)])
async def search(body: SearchRequest, session: AsyncSession = Depends(get_session)):
    """Vector search over document chunks.

    Scoped to an org (and optionally a project).  The query is embedded
    client-side using the same SentenceTransformers model that was used
    at ingestion time, then matched via cosine distance in pgvector.
    """
    try:
        results = await search_chunks(
            session,
            query=body.query,
            org_id=body.org_id,
            project_id=body.project_id,
            top_k=body.top_k,
            min_score=body.min_score,
        )
        return SearchResponse(results=results, total=len(results), query=body.query)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post('/hybrid-search', response_model=HybridSearchResponse, dependencies=[Depends(verify_internal_secret)])
async def hybrid_search(body: HybridSearchRequest, session: AsyncSession = Depends(get_session)):
    """Hybrid search: vector similarity + PostgreSQL full-text with score fusion.

    Gives you the best of both worlds — semantic understanding from vectors
    AND exact keyword matching from full-text search.

    Score = (alpha * vector_similarity) + (beta * keyword_relevance)
    Default: alpha=0.7, beta=0.3
    """
    try:
        results = await hybrid_search_chunks(
            session,
            query=body.query,
            org_id=body.org_id,
            project_id=body.project_id,
            top_k=body.top_k,
            alpha=body.alpha,
            beta=body.beta,
        )
        return HybridSearchResponse(
            results=results,
            total=len(results),
            query=body.query,
            alpha=body.alpha,
            beta=body.beta,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
