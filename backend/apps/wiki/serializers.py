from rest_framework import serializers
from .models import WikiPage, WikiPageVersion, WikiAttachment


class WikiAttachmentSerializer(serializers.ModelSerializer):
    uploadedBy = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = WikiAttachment
        fields = ('id', 'file_name', 'file_url', 'file_size', 'mime_type',
                  'uploadedBy', 'createdAt')

    def get_uploadedBy(self, obj):
        if obj.uploaded_by:
            return {'id': str(obj.uploaded_by.id), 'email': obj.uploaded_by.email}
        return None


class WikiPageVersionSerializer(serializers.ModelSerializer):
    editedBy = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = WikiPageVersion
        fields = ('id', 'version', 'title', 'content', 'summary', 'editedBy', 'createdAt')

    def get_editedBy(self, obj):
        if obj.edited_by:
            return {'id': str(obj.edited_by.id), 'email': obj.edited_by.email}
        return None


class WikiPageSerializer(serializers.ModelSerializer):
    createdBy = serializers.SerializerMethodField()
    updatedBy = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    attachmentCount = serializers.SerializerMethodField()
    childCount = serializers.SerializerMethodField()

    class Meta:
        model = WikiPage
        fields = ('id', 'title', 'slug', 'content', 'project', 'parent',
                  'createdBy', 'updatedBy', 'is_published', 'version',
                  'createdAt', 'updatedAt', 'attachmentCount', 'childCount')

    def get_createdBy(self, obj):
        if obj.created_by:
            return {'id': str(obj.created_by.id), 'email': obj.created_by.email}
        return None

    def get_updatedBy(self, obj):
        if obj.updated_by:
            return {'id': str(obj.updated_by.id), 'email': obj.updated_by.email}
        return None

    def get_attachmentCount(self, obj):
        return obj.attachments.count()

    def get_childCount(self, obj):
        return obj.children.count()


class WikiPageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPage
        fields = ('title', 'slug', 'content', 'parent', 'is_published')


class WikiPageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WikiPage
        fields = ('title', 'slug', 'content', 'parent', 'is_published')


class WikiPageTreeSerializer(serializers.ModelSerializer):
    """Lightweight serializer for building the wiki tree/sidebar."""
    children = serializers.SerializerMethodField()

    class Meta:
        model = WikiPage
        fields = ('id', 'title', 'slug', 'parent', 'version', 'children')

    def get_children(self, obj):
        qs = obj.children.filter(is_published=True)
        return WikiPageTreeSerializer(qs, many=True).data