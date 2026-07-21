from pydantic import BaseModel, Field
from typing import List, Optional


class DocumentIngestResponse(BaseModel):
    document_id: str
    chunk_count: int
    filename: str


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description='Natural language search query')
    org_id: str = Field(..., description='Organisation ID to scope the search')
    project_id: Optional[str] = Field(None, description='Optional project ID for further scoping')
    top_k: int = Field(5, ge=1, le=50, description='Max results to return')
    min_score: float = Field(0.5, ge=0.0, le=1.0, description='Minimum cosine similarity score threshold')


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str


class HybridSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    score: float
    vector_score: float
    keyword_score: float
    metadata: dict


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description='Natural language search query')
    org_id: str = Field(..., description='Organisation ID to scope the search')
    project_id: Optional[str] = Field(None, description='Optional project ID for further scoping')
    top_k: int = Field(5, ge=1, le=50, description='Max results to return')
    alpha: float = Field(0.7, ge=0.0, le=1.0, description='Vector score weight (default 0.7)')
    beta: float = Field(0.3, ge=0.0, le=1.0, description='Keyword score weight (default 0.3)')


class HybridSearchResponse(BaseModel):
    results: List[HybridSearchResult]
    total: int
    query: str
    alpha: float
    beta: float
