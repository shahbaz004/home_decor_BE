"""
Analytics models – product views and aggregated sales reports.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ProductView(TimeStampedModel):
    """A single view of a product page."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="views",
        verbose_name=_("product"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_views",
        verbose_name=_("user"),
    )
    session_key = models.CharField(_("session key"), max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)

    class Meta:
        verbose_name = _("product view")
        verbose_name_plural = _("product views")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"View of {self.product.name}"


class SalesReport(TimeStampedModel):
    """Daily aggregated sales report (populated by a scheduled Celery task)."""

    date = models.DateField(_("date"), unique=True)
    total_orders = models.PositiveIntegerField(_("total orders"), default=0)
    total_revenue = models.DecimalField(_("total revenue"), max_digits=14, decimal_places=2, default=0)
    total_items = models.PositiveIntegerField(_("total items sold"), default=0)
    new_customers = models.PositiveIntegerField(_("new customers"), default=0)

    class Meta:
        verbose_name = _("sales report")
        verbose_name_plural = _("sales reports")
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"Sales Report – {self.date}"
