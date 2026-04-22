from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Payment, Refund


class RefundInline(TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ["amount", "reason", "status", "provider_refund_id", "created_at"]
    fields = ["amount", "reason", "status", "provider_refund_id", "created_at"]


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = [
        "id",
        "order",
        "provider",
        "amount",
        "currency",
        "status",
        "provider_payment_id",
        "created_at",
    ]
    list_filter = ["provider", "status", "currency"]
    search_fields = ["order__order_number", "provider_payment_id", "provider_order_id"]
    readonly_fields = ["id", "created_at", "updated_at", "raw_response"]
    inlines = [RefundInline]


@admin.register(Refund)
class RefundAdmin(ModelAdmin):
    list_display = ["id", "payment", "amount", "reason", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["payment__order__order_number", "provider_refund_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
