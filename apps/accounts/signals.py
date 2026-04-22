"""
Signal handlers for the accounts app.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def on_user_created(sender, instance: "User", created: bool, **kwargs):
    """Send a welcome email when a new user account is created."""
    if created:
        try:
            from apps.notifications.tasks import send_welcome_email
            send_welcome_email.delay(str(instance.id))
        except Exception as exc:
            logger.warning(
                "Could not enqueue welcome email for user %s: %s",
                instance.id,
                exc,
            )
