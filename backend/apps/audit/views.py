from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import serializers as drf_serializers

from .models import AuditLog
from common.pagination import StandardPagination
from common.permissions import RoleRequiredMixin


class AuditLogSerializer(drf_serializers.ModelSerializer):
    actor = drf_serializers.SerializerMethodField()
    createdAt = drf_serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'actor', 'action', 'resource_type', 'resource_id',
                  'metadata', 'ip_address', 'createdAt')

    def get_actor(self, obj):
        if obj.actor:
            return {'id': str(obj.actor.id), 'email': obj.actor.email}
        return None


class AuditLogListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = AuditLog.objects.select_related('actor').order_by('-created_at')

        action = request.query_params.get('action')
        resource_type = request.query_params.get('resource_type')
        actor_id = request.query_params.get('actor_id')

        if action:
            qs = qs.filter(action=action)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if actor_id:
            qs = qs.filter(actor_id=actor_id)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AuditLogSerializer(page, many=True).data)


class OrgAuditLogListView(RoleRequiredMixin, APIView):
    """Org-scoped audit trail for admins."""
    required_role = 'admin'
    org_id_kwarg = 'org_id'

    def get(self, request, org_id):
        qs = AuditLog.objects.select_related('actor').order_by('-created_at')
        qs = qs.filter(metadata__organization_id=str(org_id))

        action = request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AuditLogSerializer(page, many=True).data)
