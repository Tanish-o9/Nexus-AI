"""
Tests for Enterprise Integrations
=================================
Tests for Slack, Discord, Google Calendar, Drive, Notion, Jira, Email, Webhooks, and Zapier.
"""

import pytest
from unittest.mock import AsyncMock
from app.schemas.integrations import (
    SlackMessageRequest,
    DiscordMessageRequest,
    CalendarEventRequest,
    DriveFileRequest,
    NotionPageRequest,
    JiraImportRequest,
    EmailNotificationRequest,
    WebhookCreateRequest,
    ZapierTriggerRequest,
)
from app.schemas.ai_module import AIContext
from app.services.integrations import (
    send_slack_message,
    send_discord_message,
    create_calendar_event,
    create_drive_file,
    create_notion_page,
    import_from_jira,
    send_email_notification,
    create_webhook,
    trigger_zapier,
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


# ── Slack Tests ─────────────────────────────────────────────────────────────

class TestSlackIntegration:
    @pytest.mark.asyncio
    async def test_send_slack_message(self, ai_context, mock_session):
        """Test sending Slack message."""
        request = SlackMessageRequest(
            context=ai_context,
            channel="#general",
            message="Hello from Nexus!",
        )
        
        result = await send_slack_message(mock_session, request)
        
        assert result.status == "sent"
        assert result.channel == "#general"


# ── Discord Tests ───────────────────────────────────────────────────────────

class TestDiscordIntegration:
    @pytest.mark.asyncio
    async def test_send_discord_message(self, ai_context, mock_session):
        """Test sending Discord message."""
        request = DiscordMessageRequest(
            context=ai_context,
            channel="123456789",
            message="Hello from Nexus!",
        )
        
        result = await send_discord_message(mock_session, request)
        
        assert result.status == "sent"


# ── Google Calendar Tests ───────────────────────────────────────────────────

class TestGoogleCalendar:
    @pytest.mark.asyncio
    async def test_create_calendar_event(self, ai_context, mock_session):
        """Test creating calendar event."""
        request = CalendarEventRequest(
            context=ai_context,
            summary="Team Standup",
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T11:00:00Z",
        )
        
        result = await create_calendar_event(mock_session, request)
        
        assert result.status == "created"


# ── Google Drive Tests ─────────────────────────────────────────────────────

class TestGoogleDrive:
    @pytest.mark.asyncio
    async def test_create_drive_file(self, ai_context, mock_session):
        """Test creating Drive file."""
        request = DriveFileRequest(
            context=ai_context,
            name="project-notes.txt",
            content="Project notes content",
        )
        
        result = await create_drive_file(mock_session, request)
        
        assert result.status == "created"
        assert result.name == "project-notes.txt"


# ── Notion Tests ───────────────────────────────────────────────────────────

class TestNotionIntegration:
    @pytest.mark.asyncio
    async def test_create_notion_page(self, ai_context, mock_session):
        """Test creating Notion page."""
        request = NotionPageRequest(
            context=ai_context,
            parent_id="page-123",
            title="Project Documentation",
        )
        
        result = await create_notion_page(mock_session, request)
        
        assert result.status == "created"


# ── Jira Import Tests ─────────────────────────────────────────────────────

class TestJiraImport:
    @pytest.mark.asyncio
    async def test_import_from_jira(self, ai_context, mock_session):
        """Test Jira import."""
        request = JiraImportRequest(
            context=ai_context,
            jira_url="https://company.atlassian.net",
            project_key="PROJ",
        )
        
        result = await import_from_jira(mock_session, request)
        
        assert result.status == "imported"


# ── Email Tests ─────────────────────────────────────────────────────────────

class TestEmailNotifications:
    @pytest.mark.asyncio
    async def test_send_email_notification(self, ai_context, mock_session):
        """Test sending email notification."""
        request = EmailNotificationRequest(
            context=ai_context,
            to=["user@example.com"],
            subject="Project Update",
            body="Weekly project update",
        )
        
        result = await send_email_notification(mock_session, request)
        
        assert result.status == "sent"


# ── Webhooks Tests ─────────────────────────────────────────────────────────

class TestWebhooks:
    @pytest.mark.asyncio
    async def test_create_webhook(self, ai_context, mock_session):
        """Test creating webhook."""
        request = WebhookCreateRequest(
            context=ai_context,
            url="https://example.com/webhook",
            events=["task.created", "task.completed"],
        )
        
        result = await create_webhook(mock_session, request)
        
        assert result.status == "active"


# ── Zapier Tests ───────────────────────────────────────────────────────────

class TestZapierIntegration:
    @pytest.mark.asyncio
    async def test_trigger_zapier(self, ai_context, mock_session):
        """Test triggering Zapier."""
        request = ZapierTriggerRequest(
            context=ai_context,
            zap_id="zap-123",
            payload={"task": "created"},
        )
        
        result = await trigger_zapier(mock_session, request)
        
        assert result.status == "triggered"