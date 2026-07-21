"""Custom JWT authentication that validates session (jti) is not revoked."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone


class SessionValidJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT to validate that the token's jti (session) is still active.
    
    On each authenticated request:
      - Decodes the JWT as usual
      - Looks up the UserSession by jti
      - Rejects if the session is revoked
      - Touches last_active on the session
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result

        jti = validated_token.get('jti')
        if jti is None:
            raise AuthenticationFailed('Token missing session identifier (jti).')

        from apps.accounts.models import UserSession
        try:
            session = UserSession.objects.get(jti=jti, user=user)
        except UserSession.DoesNotExist:
            raise AuthenticationFailed('Session not found. Please log in again.')

        if session.is_revoked:
            raise AuthenticationFailed('Session has been revoked. Please log in again.')

        # Touch last_active asynchronously-friendly — use update to avoid race
        UserSession.objects.filter(jti=jti).update(last_active=timezone.now())

        return user, validated_token