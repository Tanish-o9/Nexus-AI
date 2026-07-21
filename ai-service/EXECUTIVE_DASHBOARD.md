# Executive Intelligence Dashboard

## Overview

The Executive Intelligence Dashboard provides high-level insights and metrics for project management and decision-making.

## Features

### 1. Company Health
Get company-wide health metrics including velocity, productivity, and risk levels.

**Endpoint:** `POST /api/executive/health`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 2. Project Health
Get project-specific health metrics with risk factors and recommendations.

**Endpoint:** `POST /api/executive/project-health`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 3. Team Productivity
Get team productivity metrics including individual member performance.

**Endpoint:** `POST /api/executive/team-productivity`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 4. Engineering Metrics
Get DORA metrics and engineering performance indicators.

**Endpoint:** `POST /api/executive/engineering-metrics`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 5. Sprint Analytics
Get sprint performance and predictions.

**Endpoint:** `POST /api/executive/sprint-analytics`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "sprint_id": "sprint-123"
}
```

### 6. Risk Dashboard
Get risk assessment and mitigation strategies.

**Endpoint:** `POST /api/executive/risk-dashboard`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 7. AI Recommendations
Get AI-powered recommendations for process and technical improvements.

**Endpoint:** `POST /api/executive/recommendations`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 8. Cost Estimation
Get cost estimates for projects with confidence scores.

**Endpoint:** `POST /api/executive/cost-estimation`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."}
}
```

### 9. Delivery Prediction
Get delivery predictions with risk-adjusted dates.

**Endpoint:** `POST /api/executive/delivery-prediction`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "project_id": "proj-123"
}
```

### 10. Executive Summary
Get period-based executive summaries with highlights and actions.

**Endpoint:** `POST /api/executive/summary`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "period": "weekly"
}
```

## Integration

The dashboard integrates with:
- **AI Module** - Uses existing AI services for predictions
- **Knowledge Graph** - Pulls data from project entities
- **GitHub AI** - Uses repository metrics
- **Analytics** - Reuses existing analytics infrastructure