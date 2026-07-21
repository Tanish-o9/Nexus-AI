"""Enterprise security helpers — TOTP 2FA, session tracking, signed pending tokens."""

import pyotp
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserSession

TOTP_ISSUER = 'Nexus PM'
PENDING_2FA_MAX_AGE = 300  # 5 minutes


def get_client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request) -> str:
    return (request.META.get('HTTP_USER_AGENT') or '')[:512]


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_provisioning_uri(user, secret: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=TOTP_ISSUER)


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(str(code).strip(), valid_window=1)


def create_2fa_pending_token(user_id) -> str:
    from django.core.signing import TimestampSigner
    return TimestampSigner(salt='nexus-2fa-pending').sign(str(user_id))


def verify_2fa_pending_token(token: str) -> str:
    from django.core.signing import TimestampSigner
    return TimestampSigner(salt='nexus-2fa-pending').unsign(token, max_age=PENDING_2FA_MAX_AGE)


def create_user_session(user, token_or_refresh, request) -> UserSession:
    if hasattr(token_or_refresh, 'access_token'):
        token = token_or_refresh.access_token
    else:
        token = token_or_refresh
    jti = str(token['jti']) if hasattr(token, '__getitem__') else str(token)
    return UserSession.objects.create(
        user=user,
        jti=jti,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


def touch_session(jti: str) -> None:
    UserSession.objects.filter(jti=jti, is_revoked=False).update(last_active=timezone.now())


def revoke_session_by_jti(jti: str) -> None:
    UserSession.objects.filter(jti=jti).update(is_revoked=True)


def rotate_session_jti(old_jti: str, new_refresh: RefreshToken) -> None:
    session = UserSession.objects.filter(jti=old_jti, is_revoked=False).first()
    if session:
        session.jti = str(new_refresh['jti'])
        session.save(update_fields=['jti', 'last_active'])
