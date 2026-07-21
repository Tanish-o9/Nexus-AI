"""
Knowledge Graph Service
=======================
Service layer for knowledge graph operations with semantic search and graph traversal.
"""

from __future__ import annotations

import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.memory.knowledge_graph import KnowledgeEntityModel, KnowledgeRelationshipModel
from app.schemas.knowledge_graph import (
    KnowledgeEntityCreate,
    KnowledgeEntityResponse,
    KnowledgeRelationshipCreate,
    KnowledgeRelationshipResponse,
    GraphQueryRequest,
    GraphQueryResponse,
    ContextRetrievalRequest,
    ContextRetrievalResponse,
    ContextEntity,
    KnowledgeVisualizationRequest,
    KnowledgeVisualizationResponse,
    GraphNode,
    GraphEdge,
)
from app.services.embeddings import embed_text


# ── Entity Operations ─────────────────────────────────────────────────────────

async def create_entity(
    session: AsyncSession,
    entity: KnowledgeEntityCreate,
    org_id: str,
) -> KnowledgeEntityResponse:
    """Create a new knowledge graph entity."""
    embedding = None
    if entity.description:
        embedding = await embed_text(entity.description)
    
    db_entity = KnowledgeEntityModel(
        org_id=org_id,
        entity_type=entity.entity_type,
        entity_id=entity.entity_id,
        name=entity.name,
        description=entity.description,
        embedding=embedding,
        metadata_=entity.metadata,
    )
    
    session.add(db_entity)
    await session.commit()
    await session.refresh(db_entity)
    
    return KnowledgeEntityResponse(
        id=str(db_entity.id),
        org_id=db_entity.org_id,
        entity_type=db_entity.entity_type,
        entity_id=db_entity.entity_id,
        name=db_entity.name,
        description=db_entity.description,
        metadata=db_entity.metadata_,
        created_at=str(db_entity.created_at),
        updated_at=str(db_entity.updated_at),
    )


async def get_entity(
    session: AsyncSession,
    entity_id: str,
    org_id: str,
) -> Optional[KnowledgeEntityResponse]:
    """Get a knowledge graph entity by ID."""
    stmt = select(KnowledgeEntityModel).where(
        KnowledgeEntityModel.id == entity_id,
        KnowledgeEntityModel.org_id == org_id,
    )
    result = await session.execute(stmt)
    entity = result.scalar_one_or_none()
    
    if not entity:
        return None
    
    return KnowledgeEntityResponse(
        id=str(entity.id),
        org_id=entity.org_id,
        entity_type=entity.entity_type,
        entity_id=entity.entity_id,
        name=entity.name,
        description=entity.description,
        metadata=entity.metadata_,
        created_at=str(entity.created_at),
        updated_at=str(entity.updated_at),
    )


async def semantic_search_entities(
    session: AsyncSession,
    query: str,
    org_id: str,
    entity_type: Optional[str] = None,
    top_k: int = 10,
) -> List[KnowledgeEntityResponse]:
    """Search entities by semantic similarity."""
    query_embedding = await embed_text(query)
    
    stmt = select(KnowledgeEntityModel)
    stmt = stmt.where(KnowledgeEntityModel.org_id == org_id)
    if entity_type:
        stmt = stmt.where(KnowledgeEntityModel.entity_type == entity_type)
    
    # Use pgvector cosine distance
    distance_col = KnowledgeEntityModel.embedding.cosine_distance(query_embedding)
    stmt = stmt.order_by(distance_col).limit(top_k)
    
    result = await session.execute(stmt)
    entities = result.scalars().all()
    
    return [
        KnowledgeEntityResponse(
            id=str(e.id),
            org_id=e.org_id,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            name=e.name,
            description=e.description,
            metadata=e.metadata_,
            created_at=str(e.created_at),
            updated_at=str(e.updated_at),
        )
        for e in entities
    ]


# ── Relationship Operations ───────────────────────────────────────────────────

async def create_relationship(
    session: AsyncSession,
    relationship: KnowledgeRelationshipCreate,
    org_id: str,
) -> KnowledgeRelationshipResponse:
    """Create a new knowledge graph relationship."""
    db_rel = KnowledgeRelationshipModel(
        org_id=org_id,
        source_entity_id=relationship.source_entity_id,
        target_entity_id=relationship.target_entity_id,
        relationship_type=relationship.relationship_type,
        strength=relationship.strength,
        metadata_=relationship.metadata,
    )
    
    session.add(db_rel)
    await session.commit()
    await session.refresh(db_rel)
    
    return KnowledgeRelationshipResponse(
        id=str(db_rel.id),
        org_id=db_rel.org_id,
        source_entity_id=str(db_rel.source_entity_id),
        target_entity_id=str(db_rel.target_entity_id),
        relationship_type=db_rel.relationship_type,
        strength=db_rel.strength,
        metadata=db_rel.metadata_,
        created_at=str(db_rel.created_at),
    )


async def get_relationships(
    session: AsyncSession,
    entity_id: str,
    org_id: str,
    direction: str = "both",
) -> List[KnowledgeRelationshipResponse]:
    """Get relationships for an entity."""
    stmt = select(KnowledgeRelationshipModel).where(
        KnowledgeRelationshipModel.org_id == org_id,
    )
    
    if direction == "outgoing":
        stmt = stmt.where(KnowledgeRelationshipModel.source_entity_id == entity_id)
    elif direction == "incoming":
        stmt = stmt.where(KnowledgeRelationshipModel.target_entity_id == entity_id)
    else:
        stmt = stmt.where(
            (KnowledgeRelationshipModel.source_entity_id == entity_id) |
            (KnowledgeRelationshipModel.target_entity_id == entity_id)
        )
    
    result = await session.execute(stmt)
    relationships = result.scalars().all()
    
    return [
        KnowledgeRelationshipResponse(
            id=str(r.id),
            org_id=r.org_id,
            source_entity_id=str(r.source_entity_id),
            target_entity_id=str(r.target_entity_id),
            relationship_type=r.relationship_type,
            strength=r.strength,
            metadata=r.metadata_,
            created_at=str(r.created_at),
        )
        for r in relationships
    ]


# ── Graph Query ───────────────────────────────────────────────────────────────

async def query_graph(
    session: AsyncSession,
    request: GraphQueryRequest,
) -> GraphQueryResponse:
    """Query the knowledge graph with optional semantic search and traversal."""
    entities: List[KnowledgeEntityResponse] = []
    relationships: List[KnowledgeRelationshipResponse] = []
    traversal_path: List[str] = []
    
    # Semantic search if query provided
    if request.query:
        entities = await semantic_search_entities(
            session,
            request.query,
            request.context.org_id,
            request.entity_type,
            request.limit,
        )
    else:
        # Get all entities of type
        stmt = select(KnowledgeEntityModel).where(
            KnowledgeEntityModel.org_id == request.context.org_id,
        )
        if request.entity_type:
            stmt = stmt.where(KnowledgeEntityModel.entity_type == request.entity_type)
        stmt = stmt.limit(request.limit)
        
        result = await session.execute(stmt)
        db_entities = result.scalars().all()
        
        entities = [
            KnowledgeEntityResponse(
                id=str(e.id),
                org_id=e.org_id,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                name=e.name,
                description=e.description,
                metadata=e.metadata_,
                created_at=str(e.created_at),
                updated_at=str(e.updated_at),
            )
            for e in db_entities
        ]
    
    # Get relationships for found entities
    for entity in entities:
        rels = await get_relationships(session, entity.id, request.context.org_id)
        relationships.extend(rels)
        traversal_path.append(entity.id)
    
    return GraphQueryResponse(
        entities=entities,
        relationships=relationships,
        traversal_path=traversal_path,
    )


# ── Context Retrieval ─────────────────────────────────────────────────────────

async def retrieve_context(
    session: AsyncSession,
    request: ContextRetrievalRequest,
) -> ContextRetrievalResponse:
    """Retrieve relevant context from the knowledge graph."""
    all_entities: List[ContextEntity] = []
    
    # Search across different entity types
    if request.include_documents:
        doc_entities = await semantic_search_entities(
            session, request.query, request.context.org_id, "document", request.top_k
        )
        all_entities.extend([
            ContextEntity(entity=e, relevance_score=0.8) for e in doc_entities
        ])
    
    if request.include_tasks:
        task_entities = await semantic_search_entities(
            session, request.query, request.context.org_id, "task", request.top_k
        )
        all_entities.extend([
            ContextEntity(entity=e, relevance_score=0.7) for e in task_entities
        ])
    
    if request.include_users:
        user_entities = await semantic_search_entities(
            session, request.query, request.context.org_id, "user", request.top_k
        )
        all_entities.extend([
            ContextEntity(entity=e, relevance_score=0.6) for e in user_entities
        ])
    
    # Get related entities
    related_entities: List[ContextEntity] = []
    for ctx_entity in all_entities[:5]:
        rels = await get_relationships(session, ctx_entity.entity.id, request.context.org_id)
        for rel in rels:
            related = await get_entity(session, rel.target_entity_id, request.context.org_id)
            if related:
                related_entities.append(ContextEntity(entity=related, relevance_score=0.5))
    
    # Generate summary
    summary = f"Found {len(all_entities)} relevant entities"
    if all_entities:
        types = set(e.entity.entity_type for e in all_entities)
        summary += f" of types: {', '.join(types)}"
    if request.query:
        summary += f" for query: '{request.query}'"
    
    return ContextRetrievalResponse(
        entities=all_entities,
        related_entities=related_entities,
        summary=summary,
    )


# ── Knowledge Visualization ───────────────────────────────────────────────────

async def get_visualization(
    session: AsyncSession,
    request: KnowledgeVisualizationRequest,
) -> KnowledgeVisualizationResponse:
    """Get knowledge graph data for visualization."""
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    center_node: Optional[GraphNode] = None
    
    # Get center node if specified
    if request.entity_id:
        center = await get_entity(session, request.entity_id, request.context.org_id)
        if center:
            center_node = GraphNode(
                id=center.id,
                name=center.name,
                entity_type=center.entity_type,
                description=center.description,
                x=0.0,
                y=0.0,
                size=20.0,
            )
            nodes.append(center_node)
            
            # Get related entities
            rels = await get_relationships(session, request.entity_id, request.context.org_id)
            for rel in rels:
                target = await get_entity(session, rel.target_entity_id, request.context.org_id)
                if target:
                    nodes.append(GraphNode(
                        id=target.id,
                        name=target.name,
                        entity_type=target.entity_type,
                        description=target.description,
                    ))
                    edges.append(GraphEdge(
                        source=rel.source_entity_id,
                        target=rel.target_entity_id,
                        relationship_type=rel.relationship_type,
                        strength=rel.strength,
                    ))
    
    # If no center node, get all entities
    if not center_node:
        stmt = select(KnowledgeEntityModel).where(
            KnowledgeEntityModel.org_id == request.context.org_id,
        )
        if request.entity_type:
            stmt = stmt.where(KnowledgeEntityModel.entity_type == request.entity_type)
        stmt = stmt.limit(request.max_nodes)
        
        result = await session.execute(stmt)
        db_entities = result.scalars().all()
        
        for e in db_entities:
            nodes.append(GraphNode(
                id=str(e.id),
                name=e.name,
                entity_type=e.entity_type,
                description=e.description,
            ))
    
    return KnowledgeVisualizationResponse(
        nodes=nodes,
        edges=edges,
        center_node=center_node,
    )