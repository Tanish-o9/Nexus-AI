"""
Tests for Knowledge Graph
==========================
Tests for entity management, relationships, and graph operations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.schemas.knowledge_graph import (
    KnowledgeEntityCreate,
    KnowledgeRelationshipCreate,
    GraphQueryRequest,
    ContextRetrievalRequest,
    KnowledgeVisualizationRequest,
)
from app.schemas.ai_module import AIContext
from app.services.knowledge_graph import (
    create_entity,
    get_entity,
    create_relationship,
    query_graph,
    retrieve_context,
    get_visualization,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def ai_context() -> AIContext:
    """Test AI context."""
    return AIContext(
        session_id="test-session",
        user_id="test-user",
        org_id="test-org",
        project_id="test-project",
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


# ── Entity Tests ─────────────────────────────────────────────────────────────

class TestEntityOperations:
    @pytest.mark.asyncio
    async def test_create_entity(self, ai_context, mock_session):
        """Test creating a knowledge graph entity."""
        entity = KnowledgeEntityCreate(
            context=ai_context,
            entity_type="project",
            entity_id="proj-123",
            name="Test Project",
            description="A test project for knowledge graph",
        )
        
        with patch('app.services.knowledge_graph.embed_text', new_callable=AsyncMock) as mock_embed:
            with patch('app.services.knowledge_graph.KnowledgeEntityModel') as mock_model:
                mock_entity_inst = Mock()
                mock_entity_inst.id = "entity-123"
                mock_entity_inst.org_id = ai_context.org_id
                mock_entity_inst.entity_type = entity.entity_type
                mock_entity_inst.entity_id = entity.entity_id
                mock_entity_inst.name = entity.name
                mock_entity_inst.description = entity.description
                mock_entity_inst.metadata_ = entity.metadata
                mock_entity_inst.created_at = "2026-01-01T00:00:00"
                mock_entity_inst.updated_at = "2026-01-01T00:00:00"
                mock_model.return_value = mock_entity_inst
                mock_embed.return_value = [0.1, 0.2, 0.3]
                
                result = await create_entity(mock_session, entity, ai_context.org_id)
                
                assert result.entity_type == "project"
                assert result.name == "Test Project"


# ── Relationship Tests ─────────────────────────────────────────────────────────

class TestRelationshipOperations:
    @pytest.mark.asyncio
    async def test_create_relationship(self, ai_context, mock_session):
        """Test creating a knowledge graph relationship."""
        rel = KnowledgeRelationshipCreate(
            context=ai_context,
            source_entity_id="entity-1",
            target_entity_id="entity-2",
            relationship_type="references",
            strength=0.8,
        )
        
        with patch('app.services.knowledge_graph.KnowledgeRelationshipModel') as mock_model:
            mock_model.return_value = Mock(
                id="rel-123",
                org_id=ai_context.org_id,
                source_entity_id=rel.source_entity_id,
                target_entity_id=rel.target_entity_id,
                relationship_type=rel.relationship_type,
                strength=rel.strength,
                metadata_=rel.metadata,
                created_at=Mock(),
            )
            
            result = await create_relationship(mock_session, rel, ai_context.org_id)
            
            assert result.relationship_type == "references"
            assert result.strength == 0.8


# ── Graph Query Tests ─────────────────────────────────────────────────────────

class TestGraphQuery:
    @pytest.mark.asyncio
    async def test_query_graph(self, ai_context, mock_session):
        """Test querying the knowledge graph."""
        request = GraphQueryRequest(
            context=ai_context,
            entity_type="project",
            limit=10,
        )
        
        with patch('app.services.knowledge_graph.select') as mock_select:
            mock_select.return_value = Mock()
            mock_session.execute = AsyncMock()
            mock_session.execute.return_value.scalars = Mock()
            mock_session.execute.return_value.scalars.return_value.all = Mock(return_value=[])
            
            result = await query_graph(mock_session, request)
            
            assert result.entities == []
            assert result.relationships == []


# ── Context Retrieval Tests ───────────────────────────────────────────────────

class TestContextRetrieval:
    @pytest.mark.asyncio
    async def test_retrieve_context(self, ai_context, mock_session):
        """Test context retrieval from knowledge graph."""
        request = ContextRetrievalRequest(
            context=ai_context,
            query="authentication system",
            include_documents=True,
            include_tasks=True,
            include_users=True,
        )
        
        with patch('app.services.knowledge_graph.semantic_search_entities', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            result = await retrieve_context(mock_session, request)
            
            assert result.entities == []
            assert "authentication" in result.summary


# ── Visualization Tests ───────────────────────────────────────────────────────

class TestVisualization:
    @pytest.mark.asyncio
    async def test_get_visualization(self, ai_context, mock_session):
        """Test knowledge graph visualization."""
        request = KnowledgeVisualizationRequest(
            context=ai_context,
            max_depth=2,
            max_nodes=50,
        )
        
        with patch('app.services.knowledge_graph.select') as mock_select:
            mock_select.return_value = Mock()
            mock_session.execute = AsyncMock()
            mock_session.execute.return_value.scalars = Mock()
            mock_session.execute.return_value.scalars.return_value.all = Mock(return_value=[])
            
            result = await get_visualization(mock_session, request)
            
            assert result.nodes == []
            assert result.edges == []