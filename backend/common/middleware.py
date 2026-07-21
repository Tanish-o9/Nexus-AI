"""Logs permission denials and security-relevant 403 responses."""

from django.utils.deprecation import MiddlewareMixin


def _get_client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class PermissionAuditMiddleware(MiddlewareMixin):
    """
    Audit authenticated requests that receive 403 Forbidden.
    Complements DRF RBAC permission classes without replacing them.
    """

    SKIP_PREFIXES = ('/static/', '/admin/jsi18n/')

    def process_response(self, request, response):
        if response.status_code != 403:
            return response

        path = request.path
        if any(path.startswith(p) for p in self.SKIP_PREFIXES):
            return response

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return response

        from apps.audit.services import log_action
        log_action(
            actor=user,
            action='permission.denied',
            resource_type='Endpoint',
            resource_id=path,
            metadata={
                'method': request.method,
                'query': dict(request.GET),
            },
            ip_address=_get_client_ip(request),
        )
        return response
