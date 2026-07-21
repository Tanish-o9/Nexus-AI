from django.contrib.admin import AdminSite
from django.conf import settings
from django.http import HttpResponseForbidden


class NexusAdminSite(AdminSite):
    site_header = 'Nexus PM Administration'
    site_title = 'Nexus PM Admin'
    index_title = 'System Administration'

    def has_permission(self, request):
        if not super().has_permission(request):
            return False

        # In production, restrict to IP allowlist
        if not settings.DEBUG:
            allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', [])
            if allowed_ips:
                client_ip = self._get_ip(request)
                if client_ip not in allowed_ips:
                    return False

        return True

    def _get_ip(self, request) -> str:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


nexus_admin = NexusAdminSite(name='nexus_admin')
