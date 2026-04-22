"""
Product review models.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Review(TimeStampedModel):
    """A customer review for a product."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("product"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("user"),
    )
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(_("title"), max_length=200)
    body = models.TextField(_("body"))
    is_verified_purchase = models.BooleanField(_("verified purchase"), default=False)
    is_approved = models.BooleanField(_("approved"), default=False, db_index=True)

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")
        unique_together = [["product", "user"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "is_approved"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} – {self.product.name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        # Auto-verify if the user purchased this product
        if not self.pk and not self.is_verified_purchase:
            from apps.orders.models import OrderItem

            has_purchase = OrderItem.objects.filter(
                order__user=self.user,
                product=self.product,
                order__is_paid=True,
            ).exists()
            self.is_verified_purchase = has_purchase
        super().save(*args, **kwargs)


class ReviewImage(TimeStampedModel):
    """Optional images attached to a review."""

    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="images", verbose_name=_("review")
    )
    image = models.ImageField(_("image"), upload_to="reviews/")

    class Meta:
        verbose_name = _("review image")
        verbose_name_plural = _("review images")

    def __str__(self) -> str:
        return f"Image for review {self.review_id}"
