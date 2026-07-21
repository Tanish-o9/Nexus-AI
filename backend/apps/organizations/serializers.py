from rest_framework import serializers
from .models import Organization, Membership


class OrganizationSerializer(serializers.ModelSerializer):
    memberCount = serializers.IntegerField(source='memberships.count', read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'memberCount', 'created_at')


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('name',)

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters.')
        return value.strip()


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('id', 'user', 'organization', 'role', 'is_active', 'skills', 'joined_at')
        read_only_fields = ('id', 'joined_at')
