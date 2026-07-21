from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import BadSignature, SignatureExpired

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError

from django_ratelimit.decorators import ratelimit

from apps.audit.services import log_action
from common.pagination import StandardPagination

from .models import User, UserSession
from .serializers import RegisterSerializer, UserProfileSerializer
from .services import register_user, send_password_reset_email
from .security import (
    create_2fa_pending_token,
    create_user_session,
    generate_totp_secret,
    get_client_ip,
    get_totp_provisioning_uri,
    revoke_session_by_jti,
    rotate_session_jti,
    verify_2fa_pending_token,
    verify_totp,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log_auth(action: str, user, request, metadata=None):
    log_action(
        actor=user,
        action=action,
        resource_type='User',
        resource_id=str(user.id) if user else 'anonymous',
        metadata=metadata or {},
        ip_address=get_client_ip(request),
    )


def _token_response(user, request, action='auth.login', http_status=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    access['jti'] = str(refresh['jti'])
    session = create_user_session(user, access, request)
    _log_auth(action, user, request, {'session_id': str(session.id)})

    return Response({
        'user': UserProfileSerializer(user).data,
        'token': str(access),
        'refreshToken': str(refresh),
        'sessionId': str(session.id),
    }, status=http_status)


# ── Views ─────────────────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='10/h', method='POST', block=True),
    name='post'
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(**serializer.validated_data)
        return _token_response(user, request, action='auth.register', http_status=status.HTTP_201_CREATED)


@method_decorator(
    ratelimit(key='ip', rate='20/h', method='POST', block=True),
    name='post'
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            raise ValidationError({'detail': 'Email and password are required.'})

        user = authenticate(request, username=email, password=password)
        if not user:
            _log_auth('auth.login_failed', None, request, {'email': email})
            raise AuthenticationFailed('Invalid email or password.')
        if not user.is_active:
            _log_auth('auth.login_failed', user, request, {'reason': 'disabled'})
            raise AuthenticationFailed('Account is disabled.')

        if user.totp_enabled:
            return Response({
                'requires2FA': True,
                'tempToken': create_2fa_pending_token(user.id),
            })

        return _token_response(user, request)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_raw = request.data.get('refreshToken', '')
        actor = request.user if request.user.is_authenticated else None

        try:
            token = RefreshToken(refresh_raw)
            revoke_session_by_jti(str(token['jti']))
            revoke_session_by_jti(str(token.access_token['jti']))
            token.blacklist()
        except TokenError:
            pass

        if actor:
            _log_auth('auth.logout', actor, request)
        elif refresh_raw:
            _log_auth('auth.logout', None, request, {'note': 'token-only logout'})

        return Response(status=status.HTTP_204_NO_CONTENT)


class NexusTokenRefreshView(TokenRefreshView):
    """Extends SimpleJWT refresh to keep session records in sync."""

    def post(self, request, *args, **kwargs):
        old_refresh_raw = request.data.get('refresh', '')
        old_jti = None
        if old_refresh_raw:
            try:
                old_jti = str(RefreshToken(old_refresh_raw)['jti'])
            except TokenError:
                pass

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and old_jti:
            new_refresh_raw = response.data.get('refresh')
            if new_refresh_raw:
                try:
                    rotate_session_jti(old_jti, RefreshToken(new_refresh_raw))
                except TokenError:
                    pass
            else:
                from .security import touch_session
                touch_session(old_jti)

        return response


@method_decorator(
    ratelimit(key='ip', rate='5/h', method='POST', block=True),
    name='post'
)
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if email:
            send_password_reset_email(email)
        return Response({'message': 'If that email exists, a reset link has been sent.'})


@method_decorator(
    ratelimit(key='ip', rate='10/h', method='POST', block=True),
    name='post'
)
class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid', '')
        token = request.data.get('token', '')
        new_password = request.data.get('password', '')

        if not all([uid, token, new_password]):
            raise ValidationError({'detail': 'uid, token, and password are required.'})

        try:
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            raise ValidationError({'detail': 'Invalid reset link.'})

        if not default_token_generator.check_token(user, token):
            raise ValidationError({'detail': 'Reset link is invalid or has expired.'})

        user.set_password(new_password)
        user.save(update_fields=['password'])
        _log_auth('auth.password_reset', user, request)

        return Response({'message': 'Password updated successfully.'})


class MeView(APIView):
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class UserSearchListView(APIView):
    """List or search active users in the system."""

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        users = User.objects.filter(is_active=True)
        if query:
            from django.db.models import Q
            users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
        serializer = UserProfileSerializer(users[:50], many=True)
        return Response(serializer.data)


# ── 2FA ───────────────────────────────────────────────────────────────────────

class TwoFactorSetupView(APIView):
    def post(self, request):
        user = request.user
        if user.totp_enabled:
            raise ValidationError({'detail': '2FA is already enabled.'})

        secret = generate_totp_secret()
        user.totp_secret = secret
        user.save(update_fields=['totp_secret'])

        _log_auth('auth.2fa_setup_started', user, request)

        return Response({
            'secret': secret,
            'uri': get_totp_provisioning_uri(user, secret),
        })


class TwoFactorConfirmView(APIView):
    def post(self, request):
        code = request.data.get('code', '')
        user = request.user

        if not user.totp_secret:
            raise ValidationError({'detail': 'Run 2FA setup first.'})
        if not verify_totp(user.totp_secret, code):
            raise AuthenticationFailed('Invalid verification code.')

        user.totp_enabled = True
        user.save(update_fields=['totp_enabled'])
        _log_auth('auth.2fa_enabled', user, request)

        return Response({'message': 'Two-factor authentication enabled.'})


class TwoFactorDisableView(APIView):
    def post(self, request):
        code = request.data.get('code', '')
        password = request.data.get('password', '')
        user = request.user

        if not user.totp_enabled:
            raise ValidationError({'detail': '2FA is not enabled.'})
        if not user.check_password(password):
            raise AuthenticationFailed('Invalid password.')
        if not verify_totp(user.totp_secret, code):
            raise AuthenticationFailed('Invalid verification code.')

        user.totp_enabled = False
        user.totp_secret = ''
        user.save(update_fields=['totp_enabled', 'totp_secret'])
        _log_auth('auth.2fa_disabled', user, request)

        return Response({'message': 'Two-factor authentication disabled.'})


@method_decorator(
    ratelimit(key='ip', rate='20/h', method='POST', block=True),
    name='post'
)
class TwoFactorVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        temp_token = request.data.get('tempToken', '')
        code = request.data.get('code', '')

        if not temp_token or not code:
            raise ValidationError({'detail': 'tempToken and code are required.'})

        try:
            user_id = verify_2fa_pending_token(temp_token)
            user = User.objects.get(pk=user_id, is_active=True, totp_enabled=True)
        except (BadSignature, SignatureExpired, User.DoesNotExist, ValueError):
            raise AuthenticationFailed('Invalid or expired 2FA session.')

        if not verify_totp(user.totp_secret, code):
            _log_auth('auth.2fa_failed', user, request)
            raise AuthenticationFailed('Invalid verification code.')

        return _token_response(user, request, action='auth.2fa_login')


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionListView(APIView):
    def get(self, request):
        current_id = request.query_params.get('current')
        sessions = UserSession.objects.filter(user=request.user, is_revoked=False)
        data = [{
            'id': str(s.id),
            'ipAddress': s.ip_address,
            'userAgent': s.user_agent,
            'createdAt': s.created_at,
            'lastActive': s.last_active,
            'isCurrent': str(s.id) == current_id if current_id else False,
        } for s in sessions]
        return Response(data)


class SessionRevokeView(APIView):
    def delete(self, request, session_id):
        session = UserSession.objects.filter(
            pk=session_id, user=request.user, is_revoked=False
        ).first()
        if not session:
            raise ValidationError({'detail': 'Session not found.'})

        _blacklist_jti(session.jti)

        session.is_revoked = True
        session.save(update_fields=['is_revoked'])
        _log_auth('auth.session_revoked', request.user, request, {'session_id': str(session.id)})

        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionRevokeAllView(APIView):
    def post(self, request):
        keep_current = request.data.get('keepCurrent')
        qs = UserSession.objects.filter(user=request.user, is_revoked=False)
        if keep_current:
            qs = qs.exclude(pk=keep_current)

        revoked = 0
        for session in qs:
            _blacklist_jti(session.jti)
            session.is_revoked = True
            session.save(update_fields=['is_revoked'])
            revoked += 1

        _log_auth('auth.sessions_revoked_all', request.user, request, {'count': revoked})
        return Response({'revoked': revoked})


def _blacklist_jti(jti: str) -> None:
    try:
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        outstanding = OutstandingToken.objects.filter(jti=jti).first()
        if outstanding:
            BlacklistedToken.objects.get_or_create(token=outstanding)
    except Exception:
        pass


# ── Activity ──────────────────────────────────────────────────────────────────

class UserActivityView(APIView):
    """Current user's security activity log."""

    def get(self, request):
        from apps.audit.models import AuditLog
        from apps.audit.views import AuditLogSerializer

        qs = AuditLog.objects.filter(actor=request.user).order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AuditLogSerializer(page, many=True).data)
