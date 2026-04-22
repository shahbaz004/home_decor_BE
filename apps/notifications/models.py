"""
In-app notification and email log models.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """An in-app notification for a user."""

    class NotificationType(models.TextChoices):
        ORDER = "order", _("Order")
        PAYMENT = "payment", _("Payment")
        SHIPPING = "shipping", _("Shipping")
        PROMOTION = "promotion", _("Promotion")
        SYSTEM = "system", _("System")
        REVIEW = "review", _("Review")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("user"),
    )
    type = models.CharField(
        _("type"), max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM
    )
    title = models.CharField(_("title"), max_length=200)
    message = models.TextField(_("message"))
    is_read = models.BooleanField(_("read"), default=False, db_index=True)
    action_url = models.URLField(_("action URL"), blank=True)
    data = models.JSONField(_("data"), default=dict, blank=True)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} – {self.title}"


class EmailLog(TimeStampedModel):
    """Audit log of sent emails."""

    class EmailStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    to = models.EmailField(_("to"))
    subject = models.CharField(_("subject"), max_length=300)
    template = models.CharField(_("template"), max_length=100, blank=True)
    status = models.CharField(
        _("status"), max_length=10, choices=EmailStatus.choices, default=EmailStatus.PENDING
    )
    error_message = models.TextField(_("error message"), blank=True)
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True)

    class Meta:
        verbose_name = _("email log")
        verbose_name_plural = _("email logs")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Email to {self.to}: {self.subject} ({self.status})"
