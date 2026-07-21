from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .services import log_activity


@receiver(post_save, sender='projects.Task')
def on_task_activity(sender, instance, created, **kwargs):
    """Log task creation/update to activity feed."""
    if created:
        log_activity(
            project=instance.project,
            actor=instance.created_by,
            activity_type='task_created',
            description=f'Task "{instance.title}" was created',
            metadata={'task_id': str(instance.id), 'priority': instance.priority},
        )
    else:
        # Check for status change to 'done'
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status and instance.status == 'done':
            log_activity(
                project=instance.project,
                actor=instance.assignee or instance.created_by,
                activity_type='task_completed',
                description=f'Task "{instance.title}" was completed',
                metadata={'task_id': str(instance.id)},
            )


@receiver(pre_save, sender='projects.Task')
def _capture_old_task_status(sender, instance, **kwargs):
    """Store previous status for change detection."""
    if instance.pk:
        try:
            instance._old_status = sender.objects.values_list('status', flat=True).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender='projects.TaskComment')
def on_comment_activity(sender, instance, created, **kwargs):
    """Log comments to activity feed."""
    if created:
        log_activity(
            project=instance.task.project,
            actor=instance.author,
            activity_type='comment_added',
            description=f'{instance.author.username} commented on "{instance.task.title}"',
            metadata={'task_id': str(instance.task_id), 'comment_id': str(instance.id)},
        )


@receiver(post_save, sender='organizations.Membership')
def on_member_activity(sender, instance, created, **kwargs):
    """Log member joins to activity feed."""
    if created and instance.is_active:
        for project in instance.organization.projects.all():
            log_activity(
                project=project,
                actor=instance.user,
                activity_type='member_joined',
                description=f'{instance.user.username} joined the organization',
                metadata={'organization_id': str(instance.organization_id)},
            )