from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Coupon, CouponUsage


class CouponUsageInline(TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ["user", "order", "discount_amount", "created_at"]
    fields = ["user", "order", "discount_amount", "created_at"]


@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = [
        "code",
        "type",
        "value",
        "min_order_value",
        "used_count",
        "usage_limit",
        "valid_from",
        "valid_to",
        "is_active",
    ]
    list_filter = ["type", "is_active"]
    search_fields = ["code", "description"]
    filter_horizontal = ["applicable_categories", "applicable_products"]
    readonly_fields = ["id", "used_count", "created_at", "updated_at"]
    inlines = [CouponUsageInline]


@admin.register(CouponUsage)
class CouponUsageAdmin(ModelAdmin):
    list_display = ["coupon", "user", "order", "discount_amount", "created_at"]
    search_fields = ["coupon__code", "user__email", "order__order_number"]
    readonly_fields = ["id", "created_at", "updated_at"]
