from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import ShipmentTracking, ShippingRate, ShippingZone


class ShippingRateInline(TabularInline):
    model = ShippingRate
    extra = 1
    fields = ["name", "price", "is_free_above", "min_order_value", "max_order_value", "estimated_days", "is_active"]


@admin.register(ShippingZone)
class ShippingZoneAdmin(ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    inlines = [ShippingRateInline]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ShippingRate)
class ShippingRateAdmin(ModelAdmin):
    list_display = ["name", "zone", "price", "is_free_above", "estimated_days", "is_active"]
    list_filter = ["zone", "is_active"]
    search_fields = ["name", "zone__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ShipmentTracking)
class ShipmentTrackingAdmin(ModelAdmin):
    list_display = ["order", "carrier", "tracking_number", "status", "estimated_delivery"]
    list_filter = ["status", "carrier"]
    search_fields = ["order__order_number", "tracking_number"]
    readonly_fields = ["id", "created_at", "updated_at"]
