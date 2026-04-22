"""
Payment and refund models.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    class Provider(models.TextChoices):
        RAZORPAY = "razorpay", _("Razorpay")
        STRIPE = "stripe", _("Stripe")
        COD = "cod", _("Cash on Delivery")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        AUTHORIZED = "authorized", _("Authorized")
        CAPTURED = "captured", _("Captured")
        FAILED = "failed", _("Failed")
        REFUNDED = "refunded", _("Refunded")
        PARTIALLY_REFUNDED = "partially_refunded", _("Partially Refunded")

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("order"),
    )
    provider = models.CharField(_("provider"), max_length=20, choices=Provider.choices)
    amount = models.DecimalField(_("amount"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=3, default="INR")
    status = models.CharField(_("status"), max_length=25, choices=Status.choices, default=Status.PENDING)

    # Provider-specific IDs
    provider_payment_id = models.CharField(_("provider payment ID"), max_length=200, blank=True)
    provider_order_id = models.CharField(_("provider order ID"), max_length=200, blank=True, db_index=True)
    provider_signature = models.CharField(_("provider signature"), max_length=500, blank=True)

    # Raw response for audit
    raw_response = models.JSONField(_("raw response"), default=dict, blank=True)

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.provider} – {self.amount} {self.currency} ({self.status})"


class Refund(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSED = "processed", _("Processed")
        FAILED = "failed", _("Failed")

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refunds", verbose_name=_("payment")
    )
    amount = models.DecimalField(_("amount"), max_digits=12, decimal_places=2)
    reason = models.TextField(_("reason"), blank=True)
    status = models.CharField(_("status"), max_length=20, choices=Status.choices, default=Status.PENDING)
    provider_refund_id = models.CharField(_("provider refund ID"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("refund")
        verbose_name_plural = _("refunds")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Refund {self.amount} for payment {self.payment_id}"
