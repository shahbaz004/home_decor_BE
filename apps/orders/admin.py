from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderAddress, OrderItem, OrderStatusHistory


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product_name", "variant_name", "sku", "quantity", "unit_price", "total_price"]
    fields = ["product_name", "variant_name", "sku", "quantity", "unit_price", "total_price"]


class OrderAddressInline(TabularInline):
    model = OrderAddress
    extra = 0
    readonly_fields = ["type", "full_name", "phone", "street_address", "city", "state", "pincode", "country"]
    fields = ["type", "full_name", "phone", "street_address", "city", "state", "pincode", "country"]


class OrderStatusHistoryInline(TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["status", "note", "created_by", "created_at"]
    fields = ["status", "note", "created_by", "created_at"]
    ordering = ["-created_at"]


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = [
        "order_number",
        "user",
        "email",
        "status",
        "total",
        "is_paid",
        "created_at",
    ]
    list_filter = ["status", "is_paid", "created_at"]
    search_fields = ["order_number", "email", "user__email"]
    readonly_fields = ["id", "order_number", "created_at", "updated_at"]
    inlines = [OrderItemInline, OrderAddressInline, OrderStatusHistoryInline]

    fieldsets = (
        ("Order Info", {"fields": ("id", "order_number", "user", "email", "status", "is_paid")}),
        ("Financials", {"fields": ("subtotal", "discount", "shipping_cost", "tax", "total", "coupon_code")}),
        ("Notes", {"fields": ("notes",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
