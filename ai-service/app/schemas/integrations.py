"""
Enterprise Integrations Schemas
===============================
Pydantic models for enterprise integrations.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.ai_module import AIContext


# ── Slack Integration ─────────────────────────────────────────────────────────

class SlackMessageRequest(BaseModel):
    """Request to send a Slack message."""
    context: AIContext
    channel: str = Field(..., description="Slack channel ID or name")
    message: str = Field(..., description="Message to send")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Slack block kit")


class SlackMessageResponse(BaseModel):
    """Response for Slack message."""
    message_id: str
    channel: str
    status: str


# ── Discord Integration ─────────────────────────────────────────────────────────

class DiscordMessageRequest(BaseModel):
    """Request to send a Discord message."""
    context: AIContext
    channel: str = Field(..., description="Discord channel ID")
    message: str = Field(..., description="Message to send")
    embed: Optional[Dict[str, Any]] = Field(None, description="Discord embed")


class DiscordMessageResponse(BaseModel):
    """Response for Discord message."""
    message_id: str
    channel: str
    status: str


# ── Google Calendar Integration ─────────────────────────────────────────────────

class CalendarEventRequest(BaseModel):
    """Request to create a calendar event."""
    context: AIContext
    summary: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Start time ISO format")
    end_time: str = Field(..., description="End time ISO format")
    attendees: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class CalendarEventResponse(BaseModel):
    """Response for calendar event."""
    event_id: str
    status: str


# ── Google Drive Integration ──────────────────────────────────────────────────

class DriveFileRequest(BaseModel):
    """Request to create a Drive file."""
    context: AIContext
    name: str = Field(..., description="File name")
    content: str = Field(..., description="File content")
    mime_type: str = Field(default="text/plain")
    folder_id: Optional[str] = None


class DriveFileResponse(BaseModel):
    """Response for Drive file."""
    file_id: str
    name: str
    status: str


# ── Notion Integration ─────────────────────────────────────────────────────────

class NotionPageRequest(BaseModel):
    """Request to create a Notion page."""
    context: AIContext
    parent_id: str = Field(..., description="Parent page or database ID")
    title: str = Field(..., description="Page title")
    content: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class NotionPageResponse(BaseModel):
    """Response for Notion page."""
    page_id: str
    status: str


# ── Jira Import ───────────────────────────────────────────────────────────────

class JiraImportRequest(BaseModel):
    """Request to import from Jira."""
    context: AIContext
    jira_url: str = Field(..., description="Jira instance URL")
    project_key: str = Field(..., description="Jira project key")
    issue_types: Optional[List[str]] = None


class JiraImportResponse(BaseModel):
    """Response for Jira import."""
    imported_issues: int
    status: str


# ── Email Notifications ─────────────────────────────────────────────────────

class EmailNotificationRequest(BaseModel):
    """Request to send email notification."""
    context: AIContext
    to: List[str] = Field(..., description="Recipient emails")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    template: Optional[str] = None


class EmailNotificationResponse(BaseModel):
    """Response for email notification."""
    message_id: str
    status: str


# ── Webhooks ───────────────────────────────────────────────────────────────────

class WebhookCreateRequest(BaseModel):
    """Request to create a webhook."""
    context: AIContext
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to trigger on")
    secret: Optional[str] = None


class WebhookCreateResponse(BaseModel):
    """Response for webhook creation."""
    webhook_id: str
    url: str
    status: str


# ── Zapier Integration ───────────────────────────────────────────────────────

class ZapierTriggerRequest(BaseModel):
    """Request to trigger a Zapier webhook."""
    context: AIContext
    zap_id: str = Field(..., description="Zapier zap ID")
    payload: Dict[str, Any] = Field(..., description="Trigger payload")


class ZapierTriggerResponse(BaseModel):
    """Response for Zapier trigger."""
    trigger_id: str
    status: str