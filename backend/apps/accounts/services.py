from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from .models import User


def register_user(username: str, email: str, password: str) -> User:
    """Create and return a new user. Raises ValidationError on duplicate."""
    if User.objects.filter(email=email).exists():
        from rest_framework.exceptions import ValidationError
        raise ValidationError({'email': 'A user with this email already exists.'})
    user = User.objects.create_user(email=email, username=username, password=password)
    from apps.organizations.services import create_organization
    create_organization(name=f"{username}'s Workspace", created_by=user)
    return user


def send_password_reset_email(email: str) -> None:
    """Send a password reset link if the email exists. Silent if not (security)."""
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return

    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={user.pk}&token={token}"

    send_mail(
        subject='Reset your Nexus PM password',
        message=f'Click the link to reset your password: {reset_url}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True,
    )
