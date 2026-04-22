"""
Admin for the products app using Django Unfold.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Category,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    Tag,
)


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "is_primary", "display_order"]


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 0
    fields = ["name", "sku", "price_adjustment", "stock", "attributes", "is_active"]


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "parent", "is_active", "display_order", "product_count"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["id", "created_at", "updated_at"]

    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    product_count.short_description = "Products"


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        "name",
        "sku",
        "category",
        "base_price",
        "sale_price",
        "stock",
        "is_active",
        "is_featured",
        "created_at",
    ]
    list_filter = ["is_active", "is_featured", "category", "tags"]
    search_fields = ["name", "sku", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]
    filter_horizontal = ["tags"]
    inlines = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "sku", "category", "tags", "short_description", "description")}),
        ("Pricing", {"fields": ("base_price", "sale_price", "cost_price")}),
        ("Inventory", {"fields": ("stock", "low_stock_threshold")}),
        ("Physical", {"fields": ("weight", "dimensions")}),
        ("Flags", {"fields": ("is_active", "is_featured", "is_digital")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
        ("System", {"fields": ("id", "created_at", "updated_at", "deleted_at"), "classes": ("collapse",)}),
    )


class ProductAttributeValueInline(TabularInline):
    model = ProductAttributeValue
    extra = 2
    fields = ["value", "slug"]
    prepopulated_fields = {"slug": ("value",)}


@admin.register(ProductAttribute)
class ProductAttributeAdmin(ModelAdmin):
    list_display = ["name", "slug", "display_order"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductAttributeValueInline]
    readonly_fields = ["id", "created_at", "updated_at"]
