"""
Enterprise Integrations Router
=============================
FastAPI routers for enterprise integrations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import get_session
from app.schemas.integrations import (
    SlackMessageRequest,
    SlackMessageResponse,
    DiscordMessageRequest,
    DiscordMessageResponse,
    CalendarEventRequest,
    CalendarEventResponse,
    DriveFileRequest,
    DriveFileResponse,
    NotionPageRequest,
    NotionPageResponse,
    JiraImportRequest,
    JiraImportResponse,
    EmailNotificationRequest,
    EmailNotificationResponse,
    WebhookCreateRequest,
    WebhookCreateResponse,
    ZapierTriggerRequest,
    ZapierTriggerResponse,
)
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

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ── Slack Integration ─────────────────────────────────────────────────────────

@router.post(
    "/slack/message",
    response_model=SlackMessageResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Send Slack message",
)
async def slack_message_endpoint(body: SlackMessageRequest, session: AsyncSession = Depends(get_session)):
    """Send a message to Slack."""
    try:
        return await send_slack_message(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Discord Integration ─────────────────────────────────────────────────────────

@router.post(
    "/discord/message",
    response_model=DiscordMessageResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Send Discord message",
)
async def discord_message_endpoint(body: DiscordMessageRequest, session: AsyncSession = Depends(get_session)):
    """Send a message to Discord."""
    try:
        return await send_discord_message(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Google Calendar Integration ─────────────────────────────────────────────────

@router.post(
    "/calendar/event",
    response_model=CalendarEventResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Create calendar event",
)
async def calendar_event_endpoint(body: CalendarEventRequest, session: AsyncSession = Depends(get_session)):
    """Create a calendar event."""
    try:
        return await create_calendar_event(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Google Drive Integration ──────────────────────────────────────────────────

@router.post(
    "/drive/file",
    response_model=DriveFileResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Create Drive file",
)
async def drive_file_endpoint(body: DriveFileRequest, session: AsyncSession = Depends(get_session)):
    """Create a file in Google Drive."""
    try:
        return await create_drive_file(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Notion Integration ─────────────────────────────────────────────────────────

@router.post(
    "/notion/page",
    response_model=NotionPageResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Create Notion page",
)
async def notion_page_endpoint(body: NotionPageRequest, session: AsyncSession = Depends(get_session)):
    """Create a Notion page."""
    try:
        return await create_notion_page(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Jira Import ───────────────────────────────────────────────────────────────

@router.post(
    "/jira/import",
    response_model=JiraImportResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Import from Jira",
)
async def jira_import_endpoint(body: JiraImportRequest, session: AsyncSession = Depends(get_session)):
    """Import issues from Jira."""
    try:
        return await import_from_jira(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Email Notifications ─────────────────────────────────────────────────────

@router.post(
    "/email/send",
    response_model=EmailNotificationResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Send email notification",
)
async def email_notification_endpoint(body: EmailNotificationRequest, session: AsyncSession = Depends(get_session)):
    """Send an email notification."""
    try:
        return await send_email_notification(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Webhooks ───────────────────────────────────────────────────────────────────

@router.post(
    "/webhooks",
    response_model=WebhookCreateResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Create webhook",
)
async def webhook_create_endpoint(body: WebhookCreateRequest, session: AsyncSession = Depends(get_session)):
    """Create a webhook."""
    try:
        return await create_webhook(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Zapier Integration ───────────────────────────────────────────────────────

@router.post(
    "/zapier/trigger",
    response_model=ZapierTriggerResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Trigger Zapier webhook",
)
async def zapier_trigger_endpoint(body: ZapierTriggerRequest, session: AsyncSession = Depends(get_session)):
    """Trigger a Zapier webhook."""
    try:
        return await trigger_zapier(session, body)
    except Exception as exc:
        raise _error_response(exc)