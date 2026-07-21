from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .services import notify_agent_completed


class NotificationSerializer(drf_serializers.ModelSerializer):
    createdAt = drf_serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'body', 'read', 'createdAt')


class NotificationListView(APIView):
    def get(self, request):
        qs = request.user.notifications.all()[:50]
        return Response(NotificationSerializer(qs, many=True).data)


class NotificationMarkReadView(APIView):
    def patch(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.read = True
        notif.save(update_fields=['read'])
        return Response(NotificationSerializer(notif).data)


class NotificationMarkAllReadView(APIView):
    def post(self, request):
        updated = request.user.notifications.filter(read=False).update(read=True)
        return Response({'updated': updated})


class AgentCompletedView(APIView):
    """
    Internal endpoint called by the AI service when an agent finishes.
    Secured by a shared internal secret header — not a user JWT.
    """
    permission_classes = []  # Auth handled manually below

    def post(self, request):
        from django.conf import settings
        secret = request.headers.get('X-Internal-Secret', '')
        if secret != getattr(settings, 'INTERNAL_SERVICE_SECRET', ''):
            return Response(status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('userId', '')
        summary = request.data.get('summary', 'Agent task completed.')

        if not user_id:
            return Response({'error': 'userId is required.'}, status=status.HTTP_400_BAD_REQUEST)

        notify_agent_completed(user_id=user_id, task_summary=summary)
        return Response({'status': 'delivered'})
