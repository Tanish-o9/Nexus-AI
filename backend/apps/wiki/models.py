import uuid
from django.db import models
from django.conf import settings


class WikiPage(models.Model):
    """A wiki/documentation page with markdown content and version history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    content = models.TextField(blank=True, help_text='Markdown content')
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='wiki_pages'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_wiki_pages'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_wiki_pages'
    )
    is_published = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wiki_wikipage'
        ordering = ['title']
        unique_together = ('project', 'slug')
        indexes = [
            models.Index(fields=['project', 'slug']),
            models.Index(fields=['project', 'parent']),
        ]

    def __str__(self):
        return self.title


class WikiPageVersion(models.Model):
    """Version history for wiki pages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name='versions')
    version = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    summary = models.CharField(max_length=255, blank=True, help_text='Edit summary')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wiki_wikipageversion'
        ordering = ['-version']
        unique_together = ('page', 'version')

    def __str__(self):
        return f'{self.page.title} v{self.version}'


class WikiAttachment(models.Model):
    """File attachments for wiki pages. Reuses TaskAttachment pattern."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name='attachments')
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=128, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wiki_wikiattachment'
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name