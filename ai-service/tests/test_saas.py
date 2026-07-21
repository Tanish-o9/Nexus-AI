import pytest
from unittest.mock import AsyncMock
from app.schemas.saas import (
    SubscriptionPlanRequest,
    OrganizationQuotasRequest,
    UsageTrackingRequest,
    BillingInfoRequest,
    InvoiceRequest,
    TeamManagementRequest,
    FeatureFlagsRequest,
    AdminConsoleRequest,
)
from app.schemas.ai_module import AIContext
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

@pytest.fixture
def ai_context() -> AIContext:
    return AIContext(
        session_id="test-session",
        user_id="test-user",
        org_id="test-org",
        project_id="test-project",
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


class TestSubscriptionPlans:
    @pytest.mark.asyncio
    async def test_get_subscription_plans(self, ai_context, mock_session):
        request = SubscriptionPlanRequest(context=ai_context)
        result = await get_subscription_plans( mock_session, request)
        assert len(result.plans) == 2
        assert result.plans[0].name == "Free"


class TestOrganizationQuotas:
    @pytest.mark.asyncio
    async def test_get_organization_quotas(self, ai_context, mock_session):
        request = OrganizationQuotasRequest(context=ai_context)
        result = await get_organization_quotas(mock_session, request)
        assert result.projects_limit == 100
        assert "projects" in result.current_usage


class TestUsageTracking:
    @pytest.mark.asyncio
    async def test_get_usage_tracking(self, ai_context, mock_session):
        request = UsageTrackingRequest(context=ai_context)
        result = await get_usage_tracking(mock_session, request)
        assert result.period == "monthly"
        assert len(result.records) > 0


class TestBilling:
    @pytest.mark.asyncio
    async def test_get_billing_info(self, ai_context, mock_session):
        request = BillingInfoRequest(context=ai_context)
        result = await get_billing_info(mock_session, request)
        assert result.status == "active"
        assert result.amount == 29.0


class TestInvoices:
    @pytest.mark.asyncio
    async def test_get_invoices(self, ai_context, mock_session):
        request = InvoiceRequest(context=ai_context)
        result = await get_invoices(mock_session, request)
        assert len(result.invoices) > 0
        assert result.invoices[0].status == "paid"


class TestTeamManagement:
    @pytest.mark.asyncio
    async def test_get_team_management(self, ai_context, mock_session):
        request = TeamManagementRequest(context=ai_context)
        result = await get_team_management(mock_session, request)
        assert len(result.members) > 0


class TestFeatureFlags:
    @pytest.mark.asyncio
    async def test_get_feature_flags(self, ai_context, mock_session):
        request = FeatureFlagsRequest(context=ai_context)
        result = await get_feature_flags(mock_session, request)
        assert len(result.flags) > 0
        assert result.flags[0].enabled is True


class TestAdminConsole:
    @pytest.mark.asyncio
    async def test_get_admin_console(self, ai_context, mock_session):
        request = AdminConsoleRequest(context=ai_context)
        result = await get_admin_console(mock_session, request)
        assert result.stats.total_orgs == 150
        assert result.stats.mrr == 4350.0
