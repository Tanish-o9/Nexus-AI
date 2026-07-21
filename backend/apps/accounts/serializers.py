from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    organizationId = serializers.SerializerMethodField()
    totpEnabled = serializers.BooleanField(source='totp_enabled', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'organizationId', 'totpEnabled')

    def get_organizationId(self, obj):
        membership = obj.memberships.filter(is_active=True).first()
        return str(membership.organization_id) if membership else None
