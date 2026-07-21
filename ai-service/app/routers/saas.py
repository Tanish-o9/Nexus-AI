"""
SaaS Capabilities Router
========================
FastAPI routers for multi-tenancy, billing, and subscription management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import get_session
from app.schemas.saas import (
    SubscriptionPlanRequest,
    SubscriptionPlanResponse,
    OrganizationQuotasRequest,
    OrganizationQuotasResponse,
    UsageTrackingRequest,
    UsageTrackingResponse,
    BillingInfoRequest,
    BillingInfoResponse,
    InvoiceRequest,
    InvoiceResponse,
    TeamManagementRequest,
    TeamManagementResponse,
    FeatureFlagsRequest,
    FeatureFlagsResponse,
    AdminConsoleRequest,
    AdminConsoleResponse,
)
from app.services.saas import (
    get_subscription_plans,
    get_organization_quotas,
    get_usage_tracking,
    get_billing_info,
    get_invoices,
    get_team_management,
    get_feature_flags,
    get_admin_console,
)

router = APIRouter(prefix="/api/saas", tags=["saas"])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ── Subscription Plans ─────────────────────────────────────────────────────────

@router.post(
    "/plans",
    response_model=SubscriptionPlanResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get subscription plans",
)
async def subscription_plans_endpoint(body: SubscriptionPlanRequest, session: AsyncSession = Depends(get_session)):
    """Get available subscription plans."""
    try:
        return await get_subscription_plans(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Organization Quotas ───────────────────────────────────────────────────────

@router.post(
    "/quotas",
    response_model=OrganizationQuotasResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get organization quotas",
)
async def organization_quotas_endpoint(body: OrganizationQuotasRequest, session: AsyncSession = Depends(get_session)):
    """Get organization quotas."""
    try:
        return await get_organization_quotas(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Usage Tracking ───────────────────────────────────────────────────────────

@router.post(
    "/usage",
    response_model=UsageTrackingResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get usage tracking",
)
async def usage_tracking_endpoint(body: UsageTrackingRequest, session: AsyncSession = Depends(get_session)):
    """Get usage tracking data."""
    try:
        return await get_usage_tracking(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Billing ───────────────────────────────────────────────────────────────────

@router.post(
    "/billing",
    response_model=BillingInfoResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get billing info",
)
async def billing_info_endpoint(body: BillingInfoRequest, session: AsyncSession = Depends(get_session)):
    """Get billing information."""
    try:
        return await get_billing_info(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Invoices ───────────────────────────────────────────────────────────────

@router.post(
    "/invoices",
    response_model=InvoiceResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get invoices",
)
async def invoices_endpoint(body: InvoiceRequest, session: AsyncSession = Depends(get_session)):
    """Get invoices."""
    try:
        return await get_invoices(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Team Management ─────────────────────────────────────────────────────────

@router.post(
    "/team",
    response_model=TeamManagementResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get team management",
)
async def team_management_endpoint(body: TeamManagementRequest, session: AsyncSession = Depends(get_session)):
    """Get team management data."""
    try:
        return await get_team_management(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Feature Flags ───────────────────────────────────────────────────────────

@router.post(
    "/features",
    response_model=FeatureFlagsResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get feature flags",
)
async def feature_flags_endpoint(body: FeatureFlagsRequest, session: AsyncSession = Depends(get_session)):
    """Get feature flags."""
    try:
        return await get_feature_flags(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Admin Console ───────────────────────────────────────────────────────────

@router.post(
    "/admin",
    response_model=AdminConsoleResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get admin console",
)
async def admin_console_endpoint(body: AdminConsoleRequest, session: AsyncSession = Depends(get_session)):
    """Get admin console data."""
    try:
        return await get_admin_console(session, body)
    except Exception as exc:
        raise _error_response(exc)