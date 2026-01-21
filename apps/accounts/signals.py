"""
Account Signals for Audit Logging
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ActivityLog

User = get_user_model()


def log_activity(user, action, instance, changes=None):
    """활동 로그 기록 헬퍼 함수"""
    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk) if instance.pk else '',
        object_repr=str(instance)[:200],
        changes=changes or {},
    )


# User model signals are handled separately to avoid recursion
# Other models should use auditlog or manual logging
