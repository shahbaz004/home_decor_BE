"""
Coupon and coupon usage models.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Coupon(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", _("Percentage")
        FIXED = "fixed", _("Fixed Amount")
        FREE_SHIPPING = "free_shipping", _("Free Shipping")

    code = models.CharField(_("code"), max_length=50, unique=True, db_index=True)
    description = models.TextField(_("description"), blank=True)
    type = models.CharField(_("discount type"), max_length=20, choices=DiscountType.choices)
    value = models.DecimalField(
        _("value"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_("Percentage (0-100) or fixed amount."),
    )
    min_order_value = models.DecimalField(
        _("minimum order value"), max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    max_discount = models.DecimalField(
        _("maximum discount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Cap on percentage discounts."),
    )
    usage_limit = models.PositiveIntegerField(
        _("usage limit"), null=True, blank=True, help_text=_("Null means unlimited.")
    )
    usage_limit_per_user = models.PositiveIntegerField(
        _("usage limit per user"), default=1
    )
    used_count = models.PositiveIntegerField(_("used count"), default=0)
    valid_from = models.DateTimeField(_("valid from"), default=timezone.now)
    valid_to = models.DateTimeField(_("valid to"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    applicable_categories = models.ManyToManyField(
        "products.Category",
        blank=True,
        related_name="coupons",
        verbose_name=_("applicable categories"),
    )
    applicable_products = models.ManyToManyField(
        "products.Product",
        blank=True,
        related_name="coupons",
        verbose_name=_("applicable products"),
    )

    class Meta:
        verbose_name = _("coupon")
        verbose_name_plural = _("coupons")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    @property
    def is_valid(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_to and self.valid_to < now:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        return True

    def is_valid_for_user(self, user) -> bool:
        if not self.is_valid:
            return False
        usage_count = CouponUsage.objects.filter(coupon=self, user=user).count()
        return usage_count < self.usage_limit_per_user


class CouponUsage(TimeStampedModel):
    """Record of each time a coupon is used."""

    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name="usages", verbose_name=_("coupon")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        verbose_name=_("user"),
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        verbose_name=_("order"),
    )
    discount_amount = models.DecimalField(
        _("discount amount"), max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = _("coupon usage")
        verbose_name_plural = _("coupon usages")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} used {self.coupon.code}"
