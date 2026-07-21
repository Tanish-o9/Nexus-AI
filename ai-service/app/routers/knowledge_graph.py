"""
Knowledge Graph Router
======================
FastAPI routers for knowledge graph operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import get_session
from app.schemas.knowledge_graph import (
    KnowledgeEntityCreate,
    KnowledgeEntityResponse,
    KnowledgeRelationshipCreate,
    KnowledgeRelationshipResponse,
    GraphQueryRequest,
    GraphQueryResponse,
    ContextRetrievalRequest,
    ContextRetrievalResponse,
    KnowledgeVisualizationRequest,
    KnowledgeVisualizationResponse,
)
from app.services.knowledge_graph import (
    create_entity,
    get_entity,
    create_relationship,
    get_relationships,
    query_graph,
    retrieve_context,
    get_visualization,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge-graph"])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ── Entity Endpoints ─────────────────────────────────────────────────────────

@router.post(
    "/entities",
    response_model=KnowledgeEntityResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Create a knowledge graph entity",
)
async def create_entity_endpoint(body: KnowledgeEntityCreate, session: AsyncSession = Depends(get_session)):
    """Create a new entity in the knowledge graph."""
    try:
        return await create_entity(
            session=session,
            entity=body,
            org_id=body.context.org_id,
        )
    except Exception as exc:
        raise _error_response(exc)


@router.get(
    "/entities/{entity_id}",
    response_model=KnowledgeEntityResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get a knowledge graph entity",
)
async def get_entity_endpoint(entity_id: str, org_id: str, session: AsyncSession = Depends(get_session)):
    """Get a knowledge graph entity by ID."""
    try:
        result = await get_entity(
            session=session,
            entity_id=entity_id,
            org_id=org_id,
        )
        if not result:
            raise _error_response(Exception("Entity not found"), status.HTTP_404_NOT_FOUND)
        return result
    except Exception as exc:
        raise _error_response(exc)


# ── Relationship Endpoints ───────────────────────────────────────────────────

@router.post(
    "/relationships",
    response_model=KnowledgeRelationshipResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Create a knowledge graph relationship",
)
async def create_relationship_endpoint(body: KnowledgeRelationshipCreate, session: AsyncSession = Depends(get_session)):
    """Create a relationship between two entities."""
    try:
        return await create_relationship(
            session=session,
            relationship=body,
            org_id=body.context.org_id,
        )
    except Exception as exc:
        raise _error_response(exc)


@router.get(
    "/entities/{entity_id}/relationships",
    response_model=list[KnowledgeRelationshipResponse],
    dependencies=[Depends(verify_internal_secret)],
    summary="Get relationships for an entity",
)
async def get_relationships_endpoint(entity_id: str, org_id: str, direction: str = "both", session: AsyncSession = Depends(get_session)):
    """Get relationships for a specific entity."""
    try:
        return await get_relationships(
            session=session,
            entity_id=entity_id,
            org_id=org_id,
            direction=direction,
        )
    except Exception as exc:
        raise _error_response(exc)


# ── Graph Query Endpoint ─────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=GraphQueryResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Query the knowledge graph",
)
async def query_graph_endpoint(body: GraphQueryRequest, session: AsyncSession = Depends(get_session)):
    """Query the knowledge graph with semantic search and traversal."""
    try:
        return await query_graph(
            session=session,
            request=body,
        )
    except Exception as exc:
        raise _error_response(exc)


# ── Context Retrieval Endpoint ───────────────────────────────────────────────

@router.post(
    "/context",
    response_model=ContextRetrievalResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Retrieve context from the knowledge graph",
)
async def retrieve_context_endpoint(body: ContextRetrievalRequest, session: AsyncSession = Depends(get_session)):
    """Retrieve relevant context for a query."""
    try:
        return await retrieve_context(
            session=session,
            request=body,
        )
    except Exception as exc:
        raise _error_response(exc)


# ── Knowledge Visualization Endpoint ─────────────────────────────────────────

@router.post(
    "/visualize",
    response_model=KnowledgeVisualizationResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get knowledge graph visualization data",
)
async def visualize_graph_endpoint(body: KnowledgeVisualizationRequest, session: AsyncSession = Depends(get_session)):
    """Get graph data formatted for visualization."""
    try:
        return await get_visualization(
            session=session,
            request=body,
        )
    except Exception as exc:
        raise _error_response(exc)