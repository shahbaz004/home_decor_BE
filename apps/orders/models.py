"""
Order models.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.core.utils import generate_order_number


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        PROCESSING = "processing", _("Processing")
        SHIPPED = "shipped", _("Shipped")
        DELIVERED = "delivered", _("Delivered")
        CANCELLED = "cancelled", _("Cancelled")
        REFUNDED = "refunded", _("Refunded")

    order_number = models.CharField(
        _("order number"), max_length=50, unique=True, db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("user"),
    )
    email = models.EmailField(_("email"), db_index=True)
    status = models.CharField(
        _("status"), max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    # Financials
    subtotal = models.DecimalField(
        _("subtotal"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        _("discount"), max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    shipping_cost = models.DecimalField(
        _("shipping cost"), max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    tax = models.DecimalField(
        _("tax"), max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        _("total"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    coupon_code = models.CharField(_("coupon code"), max_length=50, blank=True)
    notes = models.TextField(_("order notes"), blank=True)
    is_paid = models.BooleanField(_("is paid"), default=False)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    @property
    def can_be_cancelled(self) -> bool:
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)


class OrderItem(TimeStampedModel):
    """A single line item in an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("order"))
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
        verbose_name=_("product"),
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name=_("variant"),
    )

    # Snapshot at time of purchase
    product_name = models.CharField(_("product name"), max_length=500)
    variant_name = models.CharField(_("variant name"), max_length=200, blank=True)
    sku = models.CharField(_("SKU"), max_length=100)
    quantity = models.PositiveIntegerField(_("quantity"))
    unit_price = models.DecimalField(_("unit price"), max_digits=12, decimal_places=2)
    total_price = models.DecimalField(_("total price"), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_name}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderAddress(TimeStampedModel):
    """Snapshot of a shipping/billing address for an order."""

    class AddressType(models.TextChoices):
        BILLING = "billing", _("Billing")
        SHIPPING = "shipping", _("Shipping")

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="addresses", verbose_name=_("order")
    )
    type = models.CharField(_("type"), max_length=10, choices=AddressType.choices)
    full_name = models.CharField(_("full name"), max_length=200)
    phone = models.CharField(_("phone"), max_length=20)
    street_address = models.CharField(_("street address"), max_length=500)
    apartment = models.CharField(_("apartment"), max_length=100, blank=True)
    city = models.CharField(_("city"), max_length=100)
    state = models.CharField(_("state"), max_length=100)
    pincode = models.CharField(_("pincode"), max_length=20)
    country = models.CharField(_("country"), max_length=100)

    class Meta:
        verbose_name = _("order address")
        verbose_name_plural = _("order addresses")
        unique_together = [["order", "type"]]

    def __str__(self) -> str:
        return f"{self.type.title()} address for order {self.order.order_number}"


class OrderStatusHistory(TimeStampedModel):
    """Audit trail of status changes for an order."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history", verbose_name=_("order")
    )
    status = models.CharField(_("status"), max_length=20, choices=Order.Status.choices)
    note = models.TextField(_("note"), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
        verbose_name=_("created by"),
    )

    class Meta:
        verbose_name = _("order status history")
        verbose_name_plural = _("order status histories")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order.order_number} → {self.status}"
