from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver


# ── Project deleted ───────────────────────────────────────────────────────────

@receiver(post_delete, sender='projects.Project')
def on_project_deleted(sender, instance, **kwargs):
    try:
        from .services import log_action
        actor = getattr(instance, '_deleted_by', None)
        log_action(
            actor=actor,
            action='project.delete',
            resource_type='Project',
            resource_id=getattr(instance, 'id', ''),
            metadata={
                'name': getattr(instance, 'name', ''),
                'organization_id': str(getattr(instance, 'organization_id', ''))
            },
        )
    except Exception:
        pass


# ── Membership role changed ───────────────────────────────────────────────────

@receiver(pre_save, sender='organizations.Membership')
def _capture_old_membership_role(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_role = sender.objects.values_list(
                'role', flat=True
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_role = None
    else:
        instance._old_role = None


@receiver(post_save, sender='organizations.Membership')
def on_membership_changed(sender, instance, created, **kwargs):
    from .services import log_action

    if created:
        log_action(
            actor=getattr(instance, '_changed_by', None),
            action='membership.create',
            resource_type='Membership',
            resource_id=instance.id,
            metadata={
                'user_email': instance.user.email,
                'organization_id': str(instance.organization_id),
                'role': instance.role,
            },
        )
        return

    old_role = getattr(instance, '_old_role', None)
    if old_role and old_role != instance.role:
        log_action(
            actor=getattr(instance, '_changed_by', None),
            action='membership.role_change',
            resource_type='Membership',
            resource_id=instance.id,
            metadata={
                'user_email': instance.user.email,
                'organization_id': str(instance.organization_id),
                'old_role': old_role,
                'new_role': instance.role,
            },
        )


# ── Organization deleted ──────────────────────────────────────────────────────

@receiver(post_delete, sender='organizations.Organization')
def on_org_deleted(sender, instance, **kwargs):
    from .services import log_action
    log_action(
        actor=getattr(instance, '_deleted_by', None),
        action='organization.delete',
        resource_type='Organization',
        resource_id=instance.id,
        metadata={'name': instance.name},
    )
