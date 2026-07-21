# Enterprise Knowledge Graph

## Overview

The Knowledge Graph system provides intelligent entity and relationship management for projects, documents, tasks, and users. It uses pgvector for semantic embeddings and graph structure for relationship traversal.

## Features

### 1. Project Knowledge Graph
Track project entities and their relationships.

**Entity Types:**
- `project` - Project metadata
- `task` - Task entities
- `document` - Document entities
- `user` - User expertise profiles
- `github_repo` - GitHub repository entities
- `github_pr` - Pull request entities
- `github_issue` - Issue entities

### 2. Document Relationships
Link documents to projects, tasks, and other documents.

**Relationship Types:**
- `references` - Document references another entity
- `depends_on` - Entity depends on another
- `authored_by` - Entity authored by user
- `mentions` - Entity mentions another
- `related_to` - General relationship

### 3. Task Relationships
Model task dependencies and relationships.

**Relationship Types:**
- `blocks` - Task blocks another
- `depends_on` - Task depends on another
- `parent_of` - Parent task
- `subtask_of` - Subtask relationship
- `assigned_to` - Task assigned to user

### 4. GitHub Relationships
Connect GitHub entities to projects and tasks.

**Relationship Types:**
- `implements` - PR implements task
- `fixes` - PR fixes issue
- `mentions` - PR mentions issue
- `authored_by` - PR authored by user

### 5. User Expertise Graph
Track user skills and expertise based on contributions.

**Metadata:**
- `skills` - List of skills
- `expertise_score` - Expertise level 0-1
- `contribution_count` - Number of contributions

### 6. Semantic Search
Search entities by semantic similarity using pgvector.

### 7. Context Retrieval
Retrieve relevant context for queries across entity types.

### 8. Knowledge Visualization
Get graph data formatted for visualization (nodes, edges).

## API Endpoints

### Create Entity
```
POST /api/knowledge/entities
```
```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "entity_type": "project",
  "entity_id": "proj-123",
  "name": "My Project",
  "description": "Project description"
}
```

### Get Entity
```
GET /api/knowledge/entities/{entity_id}?org_id=org-123
```

### Create Relationship
```
POST /api/knowledge/relationships
```
```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "source_entity_id": "entity-1",
  "target_entity_id": "entity-2",
  "relationship_type": "references",
  "strength": 0.8
}
```

### Query Graph
```
POST /api/knowledge/query
```
```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "entity_type": "project",
  "query": "authentication",
  "depth": 2,
  "limit": 50
}
```

### Retrieve Context
```
POST /api/knowledge/context
```
```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "query": "OAuth2 implementation",
  "include_documents": true,
  "include_tasks": true,
  "include_users": true
}
```

### Visualize Graph
```
POST /api/knowledge/visualize
```
```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "entity_id": "entity-123",
  "max_depth": 3,
  "max_nodes": 100
}
```

## Integration

The knowledge graph integrates with:
- **RAG** - Document chunks are linked to document entities
- **AI Module** - Context retrieval for AI features
- **GitHub Integration** - GitHub entities and relationships
- **Projects** - Project and task entities

## Database Schema

### Tables
- `ai_knowledge_entities` - Entity storage with pgvector embeddings
- `ai_knowledge_relationships` - Relationship graph edges

### Indexes
- HNSW vector index on entity embeddings
- Composite indexes for org/type filtering
- Indexes for relationship traversal