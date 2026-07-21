"""
SaaS Capabilities Schemas
========================
Pydantic models for multi-tenancy, billing, and subscription management.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.schemas.ai_module import AIContext


# ── Subscription Plans ─────────────────────────────────────────────────────────

class SubscriptionPlanRequest(BaseModel):
    """Request for subscription plan info."""
    context: AIContext


class SubscriptionPlan(BaseModel):
    """Subscription plan details."""
    id: str
    name: str
    price: float
    features: List[str]
    limits: Dict[str, int]


class SubscriptionPlanResponse(BaseModel):
    """Response for subscription plans."""
    plans: List[SubscriptionPlan]


# ── Organization Quotas ───────────────────────────────────────────────────────

class OrganizationQuotasRequest(BaseModel):
    """Request for organization quotas."""
    context: AIContext


class OrganizationQuotasResponse(BaseModel):
    """Response for organization quotas."""
    org_id: str
    projects_limit: int
    users_limit: int
    storage_limit: int
    api_calls_limit: int
    current_usage: Dict[str, int]


# ── Usage Tracking ───────────────────────────────────────────────────────────

class UsageTrackingRequest(BaseModel):
    """Request for usage tracking."""
    context: AIContext
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class UsageRecord(BaseModel):
    """Usage record."""
    date: str
    api_calls: int
    storage_used: int
    active_users: int


class UsageTrackingResponse(BaseModel):
    """Response for usage tracking."""
    org_id: str
    period: str
    records: List[UsageRecord]
    total: Dict[str, int]


# ── Billing ───────────────────────────────────────────────────────────────────

class BillingInfoRequest(BaseModel):
    """Request for billing info."""
    context: AIContext


class BillingInfoResponse(BaseModel):
    """Response for billing info."""
    org_id: str
    plan: str
    status: str  # active, past_due, canceled
    current_period_end: str
    amount: float


# ── Invoices ───────────────────────────────────────────────────────────────

class InvoiceRequest(BaseModel):
    """Request for invoices."""
    context: AIContext


class Invoice(BaseModel):
    """Invoice details."""
    id: str
    date: str
    amount: float
    status: str  # paid, pending, failed
    download_url: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Response for invoices."""
    invoices: List[Invoice]


# ── Team Management ─────────────────────────────────────────────────────────

class TeamManagementRequest(BaseModel):
    """Request for team management."""
    context: AIContext


class TeamMember(BaseModel):
    """Team member details."""
    user_id: str
    email: str
    role: str
    status: str


class TeamManagementResponse(BaseModel):
    """Response for team management."""
    org_id: str
    members: List[TeamMember]


# ── Feature Flags ───────────────────────────────────────────────────────────

class FeatureFlagsRequest(BaseModel):
    """Request for feature flags."""
    context: AIContext


class FeatureFlag(BaseModel):
    """Feature flag details."""
    name: str
    enabled: bool
    description: str


class FeatureFlagsResponse(BaseModel):
    """Response for feature flags."""
    flags: List[FeatureFlag]


# ── Admin Console ───────────────────────────────────────────────────────────

class AdminConsoleRequest(BaseModel):
    """Request for admin console."""
    context: AIContext


class AdminStats(BaseModel):
    """Admin statistics."""
    total_orgs: int
    total_users: int
    total_projects: int
    mrr: float  # Monthly recurring revenue
    arr: float  # Annual recurring revenue


class AdminConsoleResponse(BaseModel):
    """Response for admin console."""
    stats: AdminStats
    recent_activity: List[Dict[str, Any]]