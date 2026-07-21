"""Enterprise audit middleware — logs all authenticated API requests."""

from django.utils.deprecation import MiddlewareMixin

SKIP_PATHS = (
    '/static/', '/admin/jsi18n/', '/metrics',
    '/api/auth/token/refresh', '/api/auth/login', '/api/auth/register',
    '/api/auth/forgot-password', '/api/auth/reset-password/confirm',
    '/api/auth/2fa/verify',
)


class AuditMiddleware(MiddlewareMixin):
    """
    Logs every authenticated API request to the audit log.
    Auth events (login, logout, 2FA) are logged in accounts.views with
    richer context — this middleware captures the rest.
    """

    def process_response(self, request, response):
        path = request.path
        if any(path.startswith(p) for p in SKIP_PATHS):
            return response

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return response

        # Only log API requests
        if not path.startswith('/api/'):
            return response

        from apps.audit.services import log_action

        action_map = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        action = action_map.get(request.method, request.method.lower())

        log_action(
            actor=user,
            action=f'api.{action}',
            resource_type='Endpoint',
            resource_id=path,
            metadata={
                'method': request.method,
                'status_code': response.status_code,
                'query': dict(request.GET),
            },
            ip_address=_get_client_ip(request),
        )
        return response


def _get_client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')