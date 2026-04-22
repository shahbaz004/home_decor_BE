"""
Wishlist models.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class WishlistItem(TimeStampedModel):
    """A product (optionally with a specific variant) saved by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name=_("user"),
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name=_("product"),
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wishlist_items",
        verbose_name=_("variant"),
    )

    class Meta:
        verbose_name = _("wishlist item")
        verbose_name_plural = _("wishlist items")
        unique_together = [["user", "product", "variant"]]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} – {self.product.name}"
