"""
Knowledge Graph Schemas
=======================
Pydantic models for knowledge graph entities and relationships.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.ai_module import AIContext


# ── Entity Schemas ─────────────────────────────────────────────────────────────

class KnowledgeEntityBase(BaseModel):
    """Base schema for knowledge graph entities."""
    entity_type: str = Field(..., description="Type of entity: project, task, document, user, github_repo, etc.")
    entity_id: str = Field(..., description="External ID reference")
    name: str = Field(..., description="Entity name")
    description: Optional[str] = Field(None, description="Entity description")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class KnowledgeEntityCreate(KnowledgeEntityBase):
    """Schema for creating a knowledge entity."""
    context: AIContext


class KnowledgeEntityResponse(KnowledgeEntityBase):
    """Schema for knowledge entity response."""
    id: str = Field(..., description="Internal entity ID")
    org_id: str = Field(..., description="Organization ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


# ── Relationship Schemas ─────────────────────────────────────────────────────

class KnowledgeRelationshipBase(BaseModel):
    """Base schema for knowledge graph relationships."""
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Type: references, depends_on, authored_by, etc.")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship strength 0-1")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class KnowledgeRelationshipCreate(KnowledgeRelationshipBase):
    """Schema for creating a knowledge relationship."""
    context: AIContext


class KnowledgeRelationshipResponse(KnowledgeRelationshipBase):
    """Schema for knowledge relationship response."""
    id: str = Field(..., description="Relationship ID")
    org_id: str = Field(..., description="Organization ID")
    created_at: str = Field(..., description="Creation timestamp")


# ── Graph Query Schemas ───────────────────────────────────────────────────────

class GraphQueryRequest(BaseModel):
    """Request schema for querying the knowledge graph."""
    context: AIContext
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    query: Optional[str] = Field(None, description="Semantic search query")
    depth: int = Field(default=2, ge=1, le=5, description="Graph traversal depth")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results")


class GraphQueryResponse(BaseModel):
    """Response schema for knowledge graph query."""
    entities: list[KnowledgeEntityResponse] = Field(default_factory=list)
    relationships: list[KnowledgeRelationshipResponse] = Field(default_factory=list)
    traversal_path: list[str] = Field(default_factory=list)


# ── Context Retrieval Schemas ─────────────────────────────────────────────────

class ContextRetrievalRequest(BaseModel):
    """Request schema for context retrieval."""
    context: AIContext
    query: str = Field(..., description="Query to find relevant context")
    include_documents: bool = Field(default=True, description="Include document context")
    include_tasks: bool = Field(default=True, description="Include task context")
    include_users: bool = Field(default=True, description="Include user expertise context")
    top_k: int = Field(default=10, ge=1, le=50, description="Top K results per type")


class ContextEntity(BaseModel):
    """Context entity with relevance score."""
    entity: KnowledgeEntityResponse
    relevance_score: float = Field(..., description="Relevance score 0-1")


class ContextRetrievalResponse(BaseModel):
    """Response schema for context retrieval."""
    entities: list[ContextEntity] = Field(default_factory=list)
    related_entities: list[ContextEntity] = Field(default_factory=list)
    summary: str = Field(..., description="Context summary")


# ── Knowledge Visualization Schemas ───────────────────────────────────────────

class KnowledgeVisualizationRequest(BaseModel):
    """Request schema for knowledge graph visualization."""
    context: AIContext
    entity_id: Optional[str] = Field(None, description="Center entity for visualization")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum traversal depth")
    max_nodes: int = Field(default=100, ge=1, le=500, description="Maximum nodes to return")


class GraphNode(BaseModel):
    """Graph node for visualization."""
    id: str
    name: str
    entity_type: str
    description: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    size: Optional[float] = None


class GraphEdge(BaseModel):
    """Graph edge for visualization."""
    source: str
    target: str
    relationship_type: str
    strength: float


class KnowledgeVisualizationResponse(BaseModel):
    """Response schema for knowledge graph visualization."""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    center_node: Optional[GraphNode] = None