"""
Address models – shipping and billing addresses belonging to a user.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Address(TimeStampedModel):
    class AddressType(models.TextChoices):
        BILLING = "billing", _("Billing")
        SHIPPING = "shipping", _("Shipping")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("user"),
    )
    type = models.CharField(
        _("address type"),
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.SHIPPING,
    )
    full_name = models.CharField(_("full name"), max_length=200)
    phone = models.CharField(_("phone"), max_length=20)
    street_address = models.CharField(_("street address"), max_length=500)
    apartment = models.CharField(_("apartment / suite"), max_length=100, blank=True)
    city = models.CharField(_("city"), max_length=100)
    state = models.CharField(_("state / province"), max_length=100)
    pincode = models.CharField(_("pincode / ZIP"), max_length=20)
    country = models.CharField(_("country"), max_length=100, default="India")
    is_default = models.BooleanField(_("default address"), default=False)

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} – {self.city}, {self.state} ({self.type})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Unset any existing default of the same type for this user.
            Address.objects.filter(user=self.user, type=self.type, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)
