from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ProductView, SalesReport


@admin.register(ProductView)
class ProductViewAdmin(ModelAdmin):
    list_display = ["product", "user", "ip_address", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["product__name", "user__email", "ip_address"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SalesReport)
class SalesReportAdmin(ModelAdmin):
    list_display = ["date", "total_orders", "total_revenue", "total_items", "new_customers"]
    readonly_fields = ["id", "date", "total_orders", "total_revenue", "total_items", "new_customers", "created_at", "updated_at"]
    ordering = ["-date"]
