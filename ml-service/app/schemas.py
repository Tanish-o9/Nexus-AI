"""
Pydantic Schemas for Recommendation Inference
"""

from pydantic import BaseModel, Field


class RecommendationCandidate(BaseModel):
    project_id: str = Field(..., description="ID of the candidate project")
    user_role: str = Field("member", description="User role in context of this project (admin, member, viewer)")
    project_member_count: int = Field(0, ge=0, description="Total members in the project")
    interaction_count: int = Field(0, ge=0, description="Number of interactions between user and this project")
    recency_days: float = Field(365.0, ge=0.0, description="Days since last interaction")


class RecommendationRequest(BaseModel):
    user_id: str = Field(..., description="The user ID requesting recommendations")
    candidates: list[RecommendationCandidate] = Field(..., min_length=1, description="List of candidate projects to rank")
    top_n: int = Field(5, ge=1, description="Number of recommendations to return")


class RecommendationItem(BaseModel):
    project_id: str
    score: float = Field(..., description="Hybrid recommendation score")
    svd_score: float = Field(..., description="Raw SVD collaborative filtering score")
    xgb_score: float = Field(..., description="Raw XGBoost ranking score")


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[RecommendationItem]
