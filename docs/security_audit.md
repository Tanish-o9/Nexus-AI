# Security Hardening Pass & Audit Checklist

This audit evaluates the full Nexus PM application stack against the OWASP Top 10 security risks, covering JWT token rotation, role-based access control (RBAC), input sanitation, rate limits, edge proxies, CORS boundaries, secrets isolation, and SQL parameters.

---

## 1. Security Compliance Checklist

| Audit Item | Scope | Status | Details / Gap Explanations | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **JWT / Refresh Tokens** | Backend | **PASS** | Access + Refresh token flow implemented. Rotation enabled (`ROTATE_REFRESH_TOKENS: True`) and rotated refresh tokens are blacklisted immediately. | *Recommendation*: Reduce `ACCESS_TOKEN_LIFETIME` from 60 minutes to 15 minutes to limit the vulnerability window of leaked tokens. |
| **RBAC Integrity** | Backend | **PASS** | Organization-level roles (Owner, Admin, Member, Viewer) are checked prior to view execution using permission classes. | Ensure Django checks `IsAuthenticated` prior to role checks (`Authentication-before-Authorization` rule). |
| **Input Validation** | Full Stack | **PASS** | Django REST serializers enforce types and lengths. FastAPI uses Pydantic V2 schemas. Frontend Next.js uses strict TypeScript interfaces. | No actions required. |
| **Output Sanitization** | Frontend | **PASS** | Next.js JSX automatically escapes rendered strings by default, protecting against Cross-Site Scripting (XSS). | Review code to ensure `dangerouslySetInnerHTML` is avoided unless absolutely required. |
| **Rate Limiting** | Edge/API | **PASS** | Nginx applies global (`10r/s`) and strict auth (`1r/s` on login/register) limits. DRF integrates the `ratelimit` package. | No actions required. |
| **Security Headers** | Edge | **PASS** | Nginx injects clickjacking protection (`X-Frame-Options: DENY`), mime-sniffing protection (`X-Content-Type-Options: nosniff`), and HSTS. | No actions required. |
| **CORS Policy** | Backend | **PASS** | `CORS_ALLOWED_ORIGINS` is configured and loaded dynamically from environmental configs. Wildcards (`*`) are disallowed. | Ensure dev setting `CORS_ALLOW_ALL_ORIGINS = True` is strictly disabled in production. |
| **Secrets Handling** | Infra | **PASS** | Credentials injected dynamically via Docker Compose in development and AWS Secrets Manager at task startup in production. | Ensure `.env` is listed in all `.gitignore` configurations. |
| **Parameterized Queries**| DB Layer | **PASS** | Django ORM and SQLAlchemy generate parameterized statements natively, mitigating SQL Injection (SQLi) risks. | Do not execute raw SQL strings formatted with python string concatenation. |
| **HTTPS Enforcement** | Edge/Base | **PASS** | Nginx redirects port 80 to 443. Django production settings enforce `SECURE_SSL_REDIRECT = True` and HSTS. | Ensure HSTS preload is enabled (`SECURE_HSTS_PRELOAD = True`). |

---

## 2. Detailed Gap Analysis & Remediations

### Gap 1: Access Token Lifespan
- **Finding**: Currently, `ACCESS_TOKEN_LIFETIME` in `base.py` is set to `timedelta(minutes=60)`.
- **Risk**: If an access token is intercepted (e.g. through a leaked browser log or local storage access), the attacker has a 60-minute window to execute unauthorized actions.
- **Fix**: Update `base.py` setting `ACCESS_TOKEN_LIFETIME` to `timedelta(minutes=15)`.

### Gap 2: Safe Storage of JWTs on Frontend
- **Finding**: Frontend clients often store JWTs in local storage (`localStorage`).
- **Risk**: Local storage is vulnerable to Cross-Site Scripting (XSS) scripts, which can extract the token.
- **Fix**: Access tokens should be kept in-memory (inside React context or Redux store), and the refresh token must be stored inside a cookie configured as `HttpOnly`, `Secure`, and `SameSite=Lax`.

### Gap 3: CSRF Mitigation for WebSockets
- **Finding**: Django Channels WebSocket endpoints (`/ws/`) do not apply standard CSRF protection out of the box.
- **Risk**: Cross-Site Request Forgery via malicious tabs attempting to open persistent WebSockets on behalf of the user.
- **Fix**: Wrap Channels routing with `AllowedHostsOriginValidator` inside `core/asgi.py` to reject connections from unauthorized HTTP origins.

---

## 3. Production Environment Checklist
Before deploying the stack to AWS:
1. Run Django's built-in production deployment check:
   ```powershell
   python backend/manage.py check --deploy
   ```
2. Verify that `DEBUG = False` is set inside the environment configs (forces `prod.py` settings to load).
3. Validate that ECR/Docker image registry accesses are locked down, permitting only CI/CD GitHub runners to write.
