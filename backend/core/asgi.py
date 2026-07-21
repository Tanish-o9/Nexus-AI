import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.notifications.routing import websocket_urlpatterns as notification_ws
from apps.collaboration.routing import websocket_urlpatterns as collab_ws
from apps.notifications.middleware import JwtAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        JwtAuthMiddleware(
            URLRouter(notification_ws + collab_ws)
        )
    ),
})
