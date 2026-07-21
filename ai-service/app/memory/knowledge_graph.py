"""
Knowledge Graph Models
======================
Entity and relationship models for the enterprise knowledge graph.
Uses pgvector for semantic embeddings and graph structure for relationships.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Index, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.memory.database import Base
from app.config import get_settings


class KnowledgeEntityModel(Base):
    """Represents an entity in the knowledge graph (project, task, document, user, etc.)."""
    __tablename__ = 'ai_knowledge_entities'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # project, task, document, user, github_repo, etc.
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)  # External ID reference
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(get_settings().EMBEDDING_DIMENSION), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_knowledge_entities_org_type', 'org_id', 'entity_type'),
        Index('ix_knowledge_entities_entity', 'entity_type', 'entity_id', unique=True),
    )

    def __repr__(self):
        return f'<KnowledgeEntity type={self.entity_type} name={self.name}>'


class KnowledgeRelationshipModel(Base):
    """Represents a relationship between two entities in the knowledge graph."""
    __tablename__ = 'ai_knowledge_relationships'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('ai_knowledge_entities.id'), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('ai_knowledge_entities.id'), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # references, depends_on, authored_by, etc.
    strength: Mapped[float] = mapped_column(nullable=False, default=1.0)  # Relationship strength 0-1
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source: Mapped[KnowledgeEntityModel] = relationship('KnowledgeEntityModel', foreign_keys=[source_entity_id])
    target: Mapped[KnowledgeEntityModel] = relationship('KnowledgeEntityModel', foreign_keys=[target_entity_id])

    __table_args__ = (
        Index('ix_knowledge_relationships_org', 'org_id'),
        Index('ix_knowledge_relationships_source', 'source_entity_id', 'relationship_type'),
        Index('ix_knowledge_relationships_target', 'target_entity_id', 'relationship_type'),
    )

    def __repr__(self):
        return f'<KnowledgeRelationship type={self.relationship_type} strength={self.strength}>'