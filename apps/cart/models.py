"""
Shopping cart models – supports both authenticated users and anonymous sessions.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    """A shopping cart, optionally tied to a user or anonymous session."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
        verbose_name=_("user"),
    )
    session_key = models.CharField(_("session key"), max_length=40, null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = _("cart")
        verbose_name_plural = _("carts")

    def __str__(self) -> str:
        if self.user:
            return f"Cart of {self.user.email}"
        return f"Anonymous cart ({self.session_key})"

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def is_empty(self) -> bool:
        return not self.items.exists()


class CartItem(TimeStampedModel):
    """A single line in a shopping cart."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name=_("cart"))
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name=_("product"),
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cart_items",
        verbose_name=_("variant"),
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    unit_price = models.DecimalField(_("unit price"), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _("cart item")
        verbose_name_plural = _("cart items")
        unique_together = [["cart", "product", "variant"]]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product.name} in cart {self.cart_id}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        # Snapshot the current price at time of adding to cart
        if not self.unit_price:
            if self.variant:
                self.unit_price = self.variant.effective_price
            else:
                self.unit_price = self.product.effective_price
        super().save(*args, **kwargs)
