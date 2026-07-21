from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import status

from .models import Organization, Membership
from .serializers import OrganizationSerializer, MembershipSerializer, OrganizationUpdateSerializer
from .services import create_organization
from common.pagination import StandardPagination
from common.permissions import IsOrgAdmin, IsOrgOwner, IsSelfOrOrgAdmin, get_user_role_in_org


# ── Organization CRUD ─────────────────────────────────────────────────────────

class OrganizationListCreateView(APIView):
    def get(self, request):
        org_ids = request.user.memberships.filter(
            is_active=True
        ).values_list('organization_id', flat=True)
        qs = Organization.objects.filter(
            id__in=org_ids
        ).prefetch_related('memberships')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            OrganizationSerializer(page, many=True).data
        )

    def post(self, request):
        name = request.data.get('name', '').strip()
        if not name:
            raise ValidationError({'name': 'This field is required.'})
        org = create_organization(name=name, created_by=request.user)
        return Response(OrganizationSerializer(org).data, status=status.HTTP_201_CREATED)


class OrganizationDetailView(APIView):
    def get(self, request, pk):
        org = self._get_accessible_org(request.user, pk)
        return Response(OrganizationSerializer(org).data)

    def patch(self, request, pk):
        """Update org name. Owner only."""
        org = self._get_accessible_org(request.user, pk)
        perm = IsOrgOwner()
        if not perm.has_permission(request, self):
            raise PermissionDenied(perm.message)
        serializer = OrganizationUpdateSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrganizationSerializer(org).data)

    def delete(self, request, pk):
        """Only org owners can delete an organization."""
        org = self._get_accessible_org(request.user, pk)
        perm = IsOrgOwner()
        if not perm.has_permission(request, self):
            raise PermissionDenied(perm.message)
        org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_accessible_org(self, user, pk):
        org = get_object_or_404(Organization, pk=pk)
        if not user.memberships.filter(organization=org, is_active=True).exists():
            raise PermissionDenied('You are not a member of this organization.')
        return org


# ── Membership management (admin+) ────────────────────────────────────────────

class MemberListView(APIView):
    """List all members of an org. Requires membership (any role)."""

    def get(self, request, org_id):
        org = get_object_or_404(Organization, pk=org_id)
        self._assert_member(request.user, org)
        memberships = org.memberships.filter(
            is_active=True
        ).select_related('user')
        return Response(MembershipSerializer(memberships, many=True).data)

    def _assert_member(self, user, org):
        if not user.memberships.filter(organization=org, is_active=True).exists():
            raise PermissionDenied('You are not a member of this organization.')


class MemberInviteView(APIView):
    """Invite an existing user to an org. Requires admin+."""

    def post(self, request, org_id):
        self._assert_admin(request, org_id)
        from apps.accounts.models import User

        email = request.data.get('email', '').strip()
        role = request.data.get('role', Membership.Role.MEMBER)

        if role not in dict(Membership.Role.choices):
            raise ValidationError({'role': f'Invalid role. Choose from: {list(dict(Membership.Role.choices).keys())}'})

        # Owners can only be assigned by existing owners
        if role == Membership.Role.OWNER:
            if get_user_role_in_org(request.user, org_id) != 'owner':
                raise PermissionDenied('Only owners can assign the owner role.')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({'email': 'No user found with this email.'})

        org = get_object_or_404(Organization, pk=org_id)
        membership, created = Membership.objects.get_or_create(
            user=user, organization=org,
            defaults={'role': role, 'is_active': True},
        )
        if not created:
            if membership.is_active:
                raise ValidationError({'detail': 'User is already a member.'})
            membership.is_active = True
            membership.role = role
            membership.save(update_fields=['is_active', 'role'])

        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def _assert_admin(self, request, org_id):
        perm = IsOrgAdmin()
        if not perm.has_permission(request, type('V', (), {'kwargs': {'org_id': str(org_id)}})() ):
            raise PermissionDenied(perm.message)


class MemberRoleUpdateView(APIView):
    """Change a member's role. Requires admin+. Only owner can promote to owner."""

    def patch(self, request, org_id, membership_id):
        org = get_object_or_404(Organization, pk=org_id)
        membership = get_object_or_404(Membership, pk=membership_id, organization=org)

        actor_role = get_user_role_in_org(request.user, org_id)
        if actor_role not in ('admin', 'owner'):
            raise PermissionDenied('Admin access required.')

        new_role = request.data.get('role', '')
        if new_role not in dict(Membership.Role.choices):
            raise ValidationError({'role': 'Invalid role.'})

        if new_role == Membership.Role.OWNER and actor_role != 'owner':
            raise PermissionDenied('Only owners can assign the owner role.')

        # Prevent demoting the last owner
        if membership.role == Membership.Role.OWNER and new_role != Membership.Role.OWNER:
            owner_count = org.memberships.filter(
                role=Membership.Role.OWNER, is_active=True
            ).count()
            if owner_count <= 1:
                raise ValidationError({'detail': 'Organization must have at least one owner.'})

        membership.role = new_role
        membership.save(update_fields=['role'])
        return Response(MembershipSerializer(membership).data)


class MemberRemoveView(APIView):
    """Remove a member from an org. Requires admin+."""

    def delete(self, request, org_id, membership_id):
        org = get_object_or_404(Organization, pk=org_id)
        membership = get_object_or_404(Membership, pk=membership_id, organization=org)

        actor_role = get_user_role_in_org(request.user, org_id)
        if actor_role not in ('admin', 'owner'):
            raise PermissionDenied('Admin access required.')

        # Prevent removing the last owner
        if membership.role == Membership.Role.OWNER:
            owner_count = org.memberships.filter(
                role=Membership.Role.OWNER, is_active=True
            ).count()
            if owner_count <= 1:
                raise ValidationError({'detail': 'Cannot remove the last owner.'})

        membership.is_active = False
        membership.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MemberUpdateView(APIView):
    """Update a member's own skills (any member) or general properties (admin+)."""

    def patch(self, request, org_id, membership_id):
        org = get_object_or_404(Organization, pk=org_id)
        membership = get_object_or_404(Membership, pk=membership_id, organization=org)

        if membership.user != request.user:
            actor_role = get_user_role_in_org(request.user, org_id)
            if actor_role not in ('admin', 'owner'):
                raise PermissionDenied('You can only update your own profile/skills.')

        if 'skills' in request.data:
            skills = request.data.get('skills')
            if not isinstance(skills, list):
                raise ValidationError({'skills': 'Skills must be a list of strings.'})
            membership.skills = skills
            membership.save(update_fields=['skills'])

        return Response(MembershipSerializer(membership).data)


class MemberActivityView(APIView):
    """Retrieve recent activities/actions performed by a member."""
    permission_classes = [IsSelfOrOrgAdmin]

    def get(self, request, org_id, membership_id):
        org = get_object_or_404(Organization, pk=org_id)
        membership = get_object_or_404(Membership, pk=membership_id, organization=org)

        from apps.audit.models import AuditLog
        logs = AuditLog.objects.filter(actor=membership.user)[:50]

        data = []
        for log in logs:
            data.append({
                'id': str(log.id),
                'action': log.action,
                'resourceType': log.resource_type,
                'resourceId': log.resource_id,
                'createdAt': log.created_at,
                'metadata': log.metadata,
            })
        return Response(data)
