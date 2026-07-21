from django.contrib import admin
from core.admin import nexus_admin
from .models import AuditLog


@admin.register(AuditLog, site=nexus_admin)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'resource_type', 'resource_id', 'ip_address')
    list_filter = ('action', 'resource_type')
    search_fields = ('actor__email', 'action', 'resource_id', 'ip_address')
    readonly_fields = ('id', 'actor', 'action', 'resource_type', 'resource_id', 'metadata', 'ip_address', 'created_at')
    ordering = ('-created_at',)

    # Audit logs are immutable — disable all write operations
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
