# SaaS Capabilities

## Overview

The SaaS system provides multi-tenancy, subscription management, and billing capabilities.

## Features

### 1. Subscription Plans
Get available subscription plans.

**Endpoint:** `POST /api/saas/plans`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 2. Organization Quotas
Get organization resource quotas.

**Endpoint:** `POST /api/saas/quotas`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 3. Usage Tracking
Get usage tracking data.

**Endpoint:** `POST /api/saas/usage`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

### 4. Billing
Get billing information.

**Endpoint:** `POST /api/saas/billing`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 5. Invoices
Get invoices.

**Endpoint:** `POST /api/saas/invoices`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 6. Team Management
Get team management data.

**Endpoint:** `POST /api/saas/team`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 7. Feature Flags
Get feature flags.

**Endpoint:** `POST /api/saas/features`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 8. Admin Console
Get admin console data.

**Endpoint:** `POST /api/saas/admin`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

## Integration

The SaaS system integrates with:
- **Existing Organizations** - Reuses org structure
- **AI Module** - For usage analytics
- **Knowledge Graph** - For entity-based billing