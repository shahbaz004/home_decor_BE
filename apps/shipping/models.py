"""
Shipping zone, rate, and tracking models.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ShippingZone(TimeStampedModel):
    """A geographic zone to which shipping rates apply."""

    name = models.CharField(_("name"), max_length=200)
    countries = models.JSONField(_("countries"), default=list)  # ISO-3166-1 alpha-2 codes
    states = models.JSONField(_("states"), default=list)  # State/province names or codes
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("shipping zone")
        verbose_name_plural = _("shipping zones")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ShippingRate(TimeStampedModel):
    """A shipping rate that applies within a zone."""

    zone = models.ForeignKey(
        ShippingZone, on_delete=models.CASCADE, related_name="rates", verbose_name=_("zone")
    )
    name = models.CharField(_("name"), max_length=200)
    min_order_value = models.DecimalField(
        _("minimum order value"), max_digits=12, decimal_places=2, default=0
    )
    max_order_value = models.DecimalField(
        _("maximum order value"), max_digits=12, decimal_places=2, null=True, blank=True
    )
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2)
    is_free_above = models.DecimalField(
        _("free shipping above"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Orders above this value get free shipping."),
    )
    estimated_days = models.PositiveIntegerField(_("estimated delivery days"), default=5)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("shipping rate")
        verbose_name_plural = _("shipping rates")
        ordering = ["zone", "price"]

    def __str__(self) -> str:
        return f"{self.name} – {self.zone.name}"

    def get_price_for_order(self, order_value) -> float:
        """Return the applicable shipping price for a given order value."""
        if self.is_free_above is not None and order_value >= self.is_free_above:
            return 0
        return float(self.price)


class ShipmentTracking(TimeStampedModel):
    """Tracking information for a shipped order."""

    class TrackingStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        PICKED_UP = "picked_up", _("Picked Up")
        IN_TRANSIT = "in_transit", _("In Transit")
        OUT_FOR_DELIVERY = "out_for_delivery", _("Out for Delivery")
        DELIVERED = "delivered", _("Delivered")
        FAILED_DELIVERY = "failed_delivery", _("Failed Delivery")
        RETURNED = "returned", _("Returned")

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="tracking",
        verbose_name=_("order"),
    )
    carrier = models.CharField(_("carrier"), max_length=100)
    tracking_number = models.CharField(_("tracking number"), max_length=200, db_index=True)
    tracking_url = models.URLField(_("tracking URL"), blank=True)
    status = models.CharField(
        _("status"), max_length=30, choices=TrackingStatus.choices, default=TrackingStatus.PENDING
    )
    events = models.JSONField(_("tracking events"), default=list)
    estimated_delivery = models.DateField(_("estimated delivery"), null=True, blank=True)

    class Meta:
        verbose_name = _("shipment tracking")
        verbose_name_plural = _("shipment trackings")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.carrier} – {self.tracking_number}"
