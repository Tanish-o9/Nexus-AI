from rest_framework.permissions import BasePermission

# Hierarchy: higher index = more privilege
ROLE_HIERARCHY = ['viewer', 'member', 'admin', 'owner']


def _role_rank(role: str) -> int:
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return -1


def _get_membership(user, org_id):
    """Return the user's active membership for an org, or None."""
    return user.memberships.filter(
        organization_id=org_id, is_active=True
    ).first()


def _has_min_role(user, org_id, min_role: str) -> bool:
    membership = _get_membership(user, org_id)
    if not membership:
        return False
    return _role_rank(membership.role) >= _role_rank(min_role)


# ── Reusable permission classes ───────────────────────────────────────────────

class IsOrgMember(BasePermission):
    """User must be an active member (any role) of the org."""
    message = 'You are not a member of this organization.'

    def has_permission(self, request, view):
        org_id = _resolve_org_id(request, view)
        if not org_id:
            return True  # No org context — let view/object-level handle it
        return _has_min_role(request.user, org_id, 'viewer')


class IsOrgViewer(BasePermission):
    """Viewer or above."""
    message = 'Viewer access required.'

    def has_permission(self, request, view):
        org_id = _resolve_org_id(request, view)
        return bool(org_id and _has_min_role(request.user, org_id, 'viewer'))


class IsOrgContributor(BasePermission):
    """Member or above — can create/edit resources."""
    message = 'Member access required.'

    def has_permission(self, request, view):
        org_id = _resolve_org_id(request, view)
        return bool(org_id and _has_min_role(request.user, org_id, 'member'))


class IsOrgAdmin(BasePermission):
    """Admin or above — can manage members and settings."""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        org_id = _resolve_org_id(request, view)
        return bool(org_id and _has_min_role(request.user, org_id, 'admin'))


class IsOrgOwner(BasePermission):
    """Owner only — transfer ownership, delete org."""
    message = 'Owner access required.'

    def has_permission(self, request, view):
        org_id = _resolve_org_id(request, view)
        return bool(org_id and _has_min_role(request.user, org_id, 'owner'))


class IsSelfOrOrgAdmin(BasePermission):
    """Member viewing own data, or org admin+ viewing member data."""
    message = 'Admin access required to view other members.'

    def has_permission(self, request, view):
        org_id = view.kwargs.get('org_id')
        membership_id = view.kwargs.get('membership_id')
        if not org_id or not membership_id:
            return False

        from apps.organizations.models import Membership
        target = Membership.objects.filter(
            pk=membership_id, organization_id=org_id, is_active=True
        ).first()
        if not target:
            return True  # 404 handled by view
        if target.user_id == request.user.id:
            return _has_min_role(request.user, org_id, 'viewer')
        return _has_min_role(request.user, org_id, 'admin')


# ── Declarative mixin ─────────────────────────────────────────────────────────

class RoleRequiredMixin:
    """
    Add to any APIView to declaratively enforce a minimum role.

    Usage:
        class MyView(RoleRequiredMixin, APIView):
            required_role = 'admin'   # minimum role needed
            org_id_kwarg  = 'org_id'  # URL kwarg that holds the org PK
    """
    required_role: str = 'member'
    org_id_kwarg: str = 'org_id'

    def get_permissions(self):
        base = super().get_permissions()
        role_map = {
            'viewer': IsOrgViewer,
            'member': IsOrgContributor,
            'admin': IsOrgAdmin,
            'owner': IsOrgOwner,
        }
        cls = role_map.get(self.required_role, IsOrgContributor)
        return base + [cls()]

    def get_org_id(self):
        return self.kwargs.get(self.org_id_kwarg)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_org_id(request, view):
    """Extract org_id from URL kwargs or query params."""
    return (
        view.kwargs.get('org_id')
        or view.kwargs.get('pk')  # for org detail views
        or request.query_params.get('organization_id')
        or request.data.get('organizationId')
    )


def get_user_role_in_org(user, org_id) -> str | None:
    """Return the user's role string in an org, or None if not a member."""
    membership = _get_membership(user, org_id)
    return membership.role if membership else None
