from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


# ── Task assigned ─────────────────────────────────────────────────────────────

@receiver(pre_save, sender='projects.Task')
def _capture_old_assignee(sender, instance, **kwargs):
    """Store the previous assignee so we can detect changes in post_save."""
    if instance.pk:
        try:
            instance._old_assignee_id = sender.objects.values_list(
                'assignee_id', flat=True
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_assignee_id = None
    else:
        instance._old_assignee_id = None


@receiver(post_save, sender='projects.Task')
def on_task_saved(sender, instance, created, **kwargs):
    from .services import send_notification

    assignee = instance.assignee
    if not assignee:
        return

    old_assignee_id = getattr(instance, '_old_assignee_id', None)
    assignee_changed = created or (str(old_assignee_id) != str(assignee.id))

    if assignee_changed:
        send_notification(
            user=assignee,
            type='task_assigned',
            title='New task assigned to you',
            body=f'You have been assigned "{instance.title}" in project "{instance.project.name}".',
        )


# ── Membership created (invite accepted / added) ──────────────────────────────

@receiver(post_save, sender='organizations.Membership')
def on_membership_saved(sender, instance, created, **kwargs):
    from .services import send_notification

    if created and instance.is_active:
        send_notification(
            user=instance.user,
            type='project_update',
            title=f'You joined {instance.organization.name}',
            body=f'You are now a {instance.role} of {instance.organization.name}.',
        )


# ── Project status changed ────────────────────────────────────────────────────

@receiver(pre_save, sender='projects.Project')
def _capture_old_project_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = sender.objects.values_list(
                'status', flat=True
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender='projects.Project')
def on_project_saved(sender, instance, created, **kwargs):
    from .services import send_notification

    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status:
        # Notify all active org members
        members = instance.organization.memberships.filter(
            is_active=True
        ).select_related('user')

        for membership in members:
            send_notification(
                user=membership.user,
                type='project_update',
                title=f'Project "{instance.name}" status changed',
                body=f'Status updated from {old_status} to {instance.status}.',
            )
