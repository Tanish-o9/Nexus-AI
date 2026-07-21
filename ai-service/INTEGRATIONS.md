# Enterprise Integrations

## Overview

The Enterprise Integrations system provides connections to popular productivity and development tools.

## Features

### 1. Slack Integration
Send messages to Slack channels.

**Endpoint:** `POST /api/integrations/slack/message`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "channel": "#general",
  "message": "Hello from Nexus!",
  "blocks": []
}
```

### 2. Discord Integration
Send messages to Discord channels.

**Endpoint:** `POST /api/integrations/discord/message`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "channel": "123456789",
  "message": "Hello from Nexus!",
  "embed": {}
}
```

### 3. Google Calendar Integration
Create calendar events.

**Endpoint:** `POST /api/integrations/calendar/event`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "summary": "Team Standup",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "attendees": ["user@example.com"]
}
```

### 4. Google Drive Integration
Create files in Google Drive.

**Endpoint:** `POST /api/integrations/drive/file`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "name": "project-notes.txt",
  "content": "Project notes content",
  "mime_type": "text/plain"
}
```

### 5. Notion Integration
Create Notion pages.

**Endpoint:** `POST /api/integrations/notion/page`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "parent_id": "page-123",
  "title": "Project Documentation",
  "content": "Page content"
}
```

### 6. Jira Import
Import issues from Jira.

**Endpoint:** `POST /api/integrations/jira/import`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "jira_url": "https://company.atlassian.net",
  "project_key": "PROJ",
  "issue_types": ["Story", "Task"]
}
```

### 7. Email Notifications
Send email notifications.

**Endpoint:** `POST /api/integrations/email/send`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "to": ["user@example.com"],
  "subject": "Project Update",
  "body": "Weekly project update"
}
```

### 8. Webhooks
Create and manage webhooks.

**Endpoint:** `POST /api/integrations/webhooks`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "url": "https://example.com/webhook",
  "events": ["task.created", "task.completed"]
}
```

### 9. Zapier Integration
Trigger Zapier webhooks.

**Endpoint:** `POST /api/integrations/zapier/trigger`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "zap_id": "zap-123",
  "payload": {"task": "created"}
}
```

## Integration

All integrations are modular and can be extended. They integrate with:
- **AI Module** - For intelligent notifications
- **Knowledge Graph** - For entity synchronization
- **Executive Dashboard** - For automated reporting