# AI-Powered GitHub Integration

## Overview

The GitHub AI integration provides intelligent code analysis, review, and automation features for GitHub repositories.

## Features

### 1. Repository Indexing
Index GitHub repositories for AI analysis.

**Endpoint:** `POST /api/github-ai/index`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "branch": "main",
  "include_issues": true,
  "include_prs": true,
  "include_commits": true
}
```

### 2. Commit Analysis
Analyze commits for impact, changes, and risk.

**Endpoint:** `POST /api/github-ai/commits/analyze`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "commit_sha": "abc123"
}
```

### 3. AI Code Review
Perform AI-powered code review on pull requests.

**Endpoint:** `POST /api/github-ai/reviews`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "pr_number": 1,
  "review_type": "full"
}
```

### 4. Bug Detection
Detect potential bugs in code changes.

**Endpoint:** `POST /api/github-ai/bugs/detect`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "pr_number": 1
}
```

### 5. Security Analysis
Perform security analysis on code changes.

**Endpoint:** `POST /api/github-ai/security/analyze`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "pr_number": 1
}
```

### 6. Architecture Suggestions
Provide architecture suggestions for a repository.

**Endpoint:** `POST /api/github-ai/architecture/suggest`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "focus_area": "api"
}
```

### 7. Documentation Updates
Generate documentation updates based on PR changes.

**Endpoint:** `POST /api/github-ai/docs/update`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "pr_number": 1,
  "update_type": "api"
}
```

### 8. Commit to Task Linking
Link commits to relevant tasks using AI analysis.

**Endpoint:** `POST /api/github-ai/commits/link`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "commit_sha": "abc123"
}
```

### 9. Release Summary
Generate release summaries from tags and commits.

**Endpoint:** `POST /api/github-ai/releases/summary`

```json
{
  "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
  "owner": "octocat",
  "repo": "hello-world",
  "tag": "v1.0.0"
}
```

## Integration

The GitHub AI integration integrates with:
- **RAG** - Repository code is indexed and searchable
- **Knowledge Graph** - GitHub entities are linked to projects and tasks
- **AI Module** - Uses existing AI services for analysis
- **Existing GitHub Integration** - Reuses existing GitHub API clients