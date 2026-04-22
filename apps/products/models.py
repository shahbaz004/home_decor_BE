"""
Product catalogue models.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Category(TimeStampedModel):
    """Hierarchical product category (supports one level of parent nesting)."""

    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent category"),
    )
    image = models.ImageField(_("image"), upload_to="categories/", null=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    meta_title = models.CharField(_("meta title"), max_length=200, blank=True)
    meta_description = models.TextField(_("meta description"), blank=True)
    display_order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(TimeStampedModel):
    """Simple product tag for cross-category groupings."""

    name = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(SoftDeleteModel):
    """Core product entity."""

    name = models.CharField(_("name"), max_length=500)
    slug = models.SlugField(_("slug"), max_length=500, unique=True)
    sku = models.CharField(_("SKU"), max_length=100, unique=True, db_index=True)
    description = models.TextField(_("description"))
    short_description = models.TextField(_("short description"), blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("category"),
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products", verbose_name=_("tags"))

    # Pricing
    base_price = models.DecimalField(
        _("base price"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    sale_price = models.DecimalField(
        _("sale price"), max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    cost_price = models.DecimalField(
        _("cost price"), max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )

    # Inventory
    stock = models.PositiveIntegerField(_("stock"), default=0)
    low_stock_threshold = models.PositiveIntegerField(_("low stock threshold"), default=5)

    # Flags
    is_active = models.BooleanField(_("active"), default=True)
    is_featured = models.BooleanField(_("featured"), default=False)
    is_digital = models.BooleanField(_("digital product"), default=False)

    # Physical attributes
    weight = models.DecimalField(_("weight (kg)"), max_digits=8, decimal_places=3, null=True, blank=True)
    dimensions = models.JSONField(_("dimensions"), default=dict, blank=True)  # {length, width, height}

    # SEO
    meta_title = models.CharField(_("meta title"), max_length=200, blank=True)
    meta_description = models.TextField(_("meta description"), blank=True)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        """Return sale price if set, otherwise base price."""
        return self.sale_price if self.sale_price is not None else self.base_price

    @property
    def discount_percentage(self) -> int:
        if self.sale_price and self.base_price and self.base_price > 0:
            return int(((self.base_price - self.sale_price) / self.base_price) * 100)
        return 0

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock <= self.low_stock_threshold


class ProductImage(TimeStampedModel):
    """Images attached to a product."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", verbose_name=_("product")
    )
    image = models.ImageField(_("image"), upload_to="products/")
    alt_text = models.CharField(_("alt text"), max_length=300, blank=True)
    is_primary = models.BooleanField(_("primary image"), default=False)
    display_order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("product image")
        verbose_name_plural = _("product images")
        ordering = ["display_order", "-is_primary"]

    def __str__(self) -> str:
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class ProductVariant(TimeStampedModel):
    """
    A purchasable variant of a product (e.g. 'Blue / Large').
    Price adjustments are relative to the parent product's effective_price.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants", verbose_name=_("product")
    )
    name = models.CharField(_("variant name"), max_length=200)
    sku = models.CharField(_("SKU"), max_length=100, unique=True, db_index=True)
    price_adjustment = models.DecimalField(
        _("price adjustment"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Added to the product price. Use negative values for discounts."),
    )
    stock = models.PositiveIntegerField(_("stock"), default=0)
    attributes = models.JSONField(_("attributes"), default=dict)  # e.g. {"color": "blue", "size": "L"}
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("product variant")
        verbose_name_plural = _("product variants")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.product.name} – {self.name}"

    @property
    def effective_price(self):
        return self.product.effective_price + self.price_adjustment


class ProductAttribute(TimeStampedModel):
    """Attribute definition (e.g. Color, Size, Material)."""

    name = models.CharField(_("name"), max_length=100, unique=True)
    slug = models.SlugField(_("slug"), max_length=100, unique=True)
    display_order = models.PositiveIntegerField(_("display order"), default=0)

    class Meta:
        verbose_name = _("product attribute")
        verbose_name_plural = _("product attributes")
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductAttributeValue(TimeStampedModel):
    """Possible values for a ``ProductAttribute`` (e.g. "Red", "XL")."""

    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name=_("attribute"),
    )
    value = models.CharField(_("value"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=200)

    class Meta:
        verbose_name = _("attribute value")
        verbose_name_plural = _("attribute values")
        unique_together = [["attribute", "value"]]
        ordering = ["value"]

    def __str__(self) -> str:
        return f"{self.attribute.name}: {self.value}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.value)
        super().save(*args, **kwargs)
