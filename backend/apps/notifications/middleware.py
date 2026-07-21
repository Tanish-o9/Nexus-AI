from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


@database_sync_to_async
def get_user_from_token(token_str):
    from apps.accounts.models import User
    try:
        token = AccessToken(token_str)
        return User.objects.get(id=token['user_id'])
    except (TokenError, User.DoesNotExist):
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token_list = params.get('token', [])
        token_str = token_list[0] if token_list else None

        scope['user'] = (
            await get_user_from_token(token_str) if token_str else AnonymousUser()
        )
        return await super().__call__(scope, receive, send)
