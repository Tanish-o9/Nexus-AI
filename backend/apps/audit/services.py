from django.db import transaction
from .models import AuditLog


def log_action(
    actor,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict = None,
    ip_address: str = None,
) -> None:
    """
    Schedule an audit log write after the current transaction commits.
    Safe to call from signals, views, or services — never blocks the caller.
    """
    def _write():
        try:
            AuditLog.objects.create(
                actor=actor if getattr(actor, 'pk', None) else None,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                metadata=metadata or {},
                ip_address=ip_address,
            )
        except Exception:
            pass

    try:
        transaction.on_commit(_write)
    except Exception:
        _write()
