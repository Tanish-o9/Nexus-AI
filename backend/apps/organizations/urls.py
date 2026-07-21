from django.urls import path
from apps.audit.views import OrgAuditLogListView
from .views import (
    OrganizationListCreateView, OrganizationDetailView,
    MemberListView, MemberInviteView,
    MemberRoleUpdateView, MemberRemoveView,
    MemberUpdateView, MemberActivityView
)

urlpatterns = [
    path('', OrganizationListCreateView.as_view(), name='org-list-create'),
    path('<uuid:pk>/', OrganizationDetailView.as_view(), name='org-detail'),
    path('<uuid:pk>', OrganizationDetailView.as_view()),

    # Member management
    path('<uuid:org_id>/members/', MemberListView.as_view(), name='org-members'),
    path('<uuid:org_id>/members', MemberListView.as_view()),
    path('<uuid:org_id>/members/invite/', MemberInviteView.as_view(), name='org-invite'),
    path('<uuid:org_id>/members/invite', MemberInviteView.as_view()),
    path('<uuid:org_id>/members/<uuid:membership_id>/role/', MemberRoleUpdateView.as_view(), name='org-member-role'),
    path('<uuid:org_id>/members/<uuid:membership_id>/role', MemberRoleUpdateView.as_view()),
    path('<uuid:org_id>/members/<uuid:membership_id>/', MemberRemoveView.as_view(), name='org-member-remove'),
    path('<uuid:org_id>/members/<uuid:membership_id>', MemberRemoveView.as_view()),
    
    path('<uuid:org_id>/members/<uuid:membership_id>/update/', MemberUpdateView.as_view()),
    path('<uuid:org_id>/members/<uuid:membership_id>/update', MemberUpdateView.as_view()),
    path('<uuid:org_id>/members/<uuid:membership_id>/activity/', MemberActivityView.as_view()),
    path('<uuid:org_id>/members/<uuid:membership_id>/activity', MemberActivityView.as_view()),

    path('<uuid:org_id>/audit/', OrgAuditLogListView.as_view(), name='org-audit'),
    path('<uuid:org_id>/audit', OrgAuditLogListView.as_view()),
]
