from django.urls import path, re_path
from .views import (
    RegisterView, LoginView, LogoutView, NexusTokenRefreshView,
    ForgotPasswordView, ResetPasswordConfirmView, MeView, UserSearchListView,
    TwoFactorSetupView, TwoFactorConfirmView, TwoFactorDisableView, TwoFactorVerifyView,
    SessionListView, SessionRevokeView, SessionRevokeAllView, UserActivityView,
)

urlpatterns = [
    re_path(r'^register/?$', RegisterView.as_view(), name='auth-register'),
    re_path(r'^login/?$', LoginView.as_view(), name='auth-login'),
    re_path(r'^logout/?$', LogoutView.as_view(), name='auth-logout'),
    re_path(r'^token/refresh/?$', NexusTokenRefreshView.as_view(), name='auth-token-refresh'),
    re_path(r'^forgot-password/?$', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    re_path(r'^reset-password/confirm/?$', ResetPasswordConfirmView.as_view(), name='auth-reset-confirm'),
    re_path(r'^me/?$', MeView.as_view(), name='auth-me'),
    re_path(r'^users/?$', UserSearchListView.as_view(), name='auth-users'),

    # 2FA
    re_path(r'^2fa/setup/?$', TwoFactorSetupView.as_view(), name='auth-2fa-setup'),
    re_path(r'^2fa/confirm/?$', TwoFactorConfirmView.as_view(), name='auth-2fa-confirm'),
    re_path(r'^2fa/disable/?$', TwoFactorDisableView.as_view(), name='auth-2fa-disable'),
    re_path(r'^2fa/verify/?$', TwoFactorVerifyView.as_view(), name='auth-2fa-verify'),

    # Sessions
    re_path(r'^sessions/?$', SessionListView.as_view(), name='auth-sessions'),
    re_path(r'^sessions/revoke-all/?$', SessionRevokeAllView.as_view(), name='auth-sessions-revoke-all'),
    re_path(r'^sessions/(?P<session_id>[0-9a-f-]+)/?$', SessionRevokeView.as_view(), name='auth-session-revoke'),

    # Activity
    re_path(r'^activity/?$', UserActivityView.as_view(), name='auth-activity'),
]
