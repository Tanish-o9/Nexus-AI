# Nexus PM — API Style Guide & Standards

This document establishes the official REST API design standards for the Nexus PM ecosystem (including Django Backend and FastAPI AI/ML microservices) to ensure consistency, security, and developer productivity.

---

## 1. API Versioning & Routing

### 1.1 Versioning Scheme
- All public-facing and frontend-consumed REST APIs must be explicitly versioned via the URL path.
- The default current API path prefix is `/api/v1/`.
  - **Correct**: `/api/v1/projects/`
  - **Incorrect**: `/api/projects/` (these legacy routes should be migrated to `v1`)

### 1.2 Internal Service Routing
- Endpoints designed strictly for communication between microservices (e.g., FastAPI calling Django or Django calling ML/AI service) must use the `/api/internal/` prefix.
  - **Example**: `/api/internal/projects/<uuid:pk>/overview/`
  - Internal routes must bypass public OAuth/JWT verification and authenticate via a shared service secret header (`X-Internal-Secret`).

---

## 2. Response Payloads & Envelope Shape

### 2.1 Casing Conventions
- **API Boundary**: All JSON request and response payloads must use **camelCase** keys to align with frontend JavaScript conventions.
  - **Example**: `{"organizationId": "...", "dueDate": "..."}`
- **Backend Internal**: Python microservices map these to **snake_case** (e.g. `organization_id`, `due_date`) during validation/deserialization.

### 2.2 List Pagination Envelope
All listing endpoints that return multiple items must enforce pagination and wrap results in a standard envelope:
```json
{
  "count": 125,
  "next": "https://api.nexus-pm.com/api/v1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "8fa85b9e-648c-4a37-b4d2-7fb7e6717a02",
      "name": "Acme Website redesign",
      "status": "active"
    }
  ]
}
```

### 2.3 Exception/Error Envelope
All errors (including model validation errors and system exceptions) must be caught and serialized into a uniform error response envelope:
```json
{
  "error": "error_code_string",
  "detail": "Description of the error or a structured field validation dictionary"
}
```
#### Standard Error Codes:
- `bad_request` (HTTP 400)
- `unauthorized` (HTTP 401)
- `forbidden` (HTTP 403)
- `not_found` (HTTP 404)
- `method_not_allowed` (HTTP 405)
- `conflict` (HTTP 409)
- `too_many_requests` (HTTP 429)
- `internal_server_error` (HTTP 500)

---

## 3. Query Parameters: Filtering, Sorting, & Slicing

### 3.1 Filtering
- Filters are passed as query parameters in camelCase.
- **Example**: `GET /api/v1/projects/?organizationId=uuid&status=active`
- Implement custom `FilterSet` subclasses (using `django-filter` or Pydantic validation) to strictly define allowed filter fields and prevent random SQL parameter injection.

### 3.2 Sorting (Ordering)
- Sorting is controlled via the `ordering` query parameter.
- Default sorting direction is ascending. Descending is denoted by a leading minus sign (`-`).
- **Example**: `GET /api/v1/projects/?ordering=-updatedAt` (orders by last updated, newest first).
- Every endpoint must define an explicit whitelist of allowed ordering fields in the views to avoid database index mismatches and performance degradation.

---

## 4. HTTP Status Code Mapping

Always return the correct semantic HTTP code for every response:

| HTTP Status | Casing/Use Case | Description |
| :--- | :--- | :--- |
| **200 OK** | Successful Read/Update | Payload returned. |
| **201 Created** | Successful Write | Object successfully persisted; returns created model. |
| **204 No Content** | Successful Delete | Operation complete; no response payload returned. |
| **400 Bad Request** | Validation Failure | Invalid fields or payload syntax; returns validation dict. |
| **401 Unauthorized** | Missing/Expired Auth | Invalid token or missing credentials. |
| **403 Forbidden** | RBAC Privilege Block | Authenticated user lacks privileges (e.g. Viewer attempting write). |
| **404 Not Found** | Missing Resource | ID does not map to any record. |
| **429 Too Many Requests**| Rate Limit Crossed | Request frequency exceeds threshold limits. |
| **500 Internal Error** | Uncaught System Crash | Server-side error; returns masked generic message. |

---

## 5. Security Standards

1. **Authentication Header**: External APIs require `Authorization: Bearer <JWT_TOKEN>`.
2. **CORS Policy**: CORS must be strictly locked down in production to exclude wildcard origins (`*`). Only allow verified frontend origins.
3. **Internal Auth Header**: Microservice-to-microservice traffic is verified using the `X-Internal-Secret` header.
4. **Rate Limiting**: Rate limiting must be active on auth endpoints (e.g. `/api/v1/auth/login/`: 5 requests/min per IP) to mitigate brute-force attacks.
