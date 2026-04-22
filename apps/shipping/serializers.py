from rest_framework import serializers

from .models import ShipmentTracking, ShippingRate, ShippingZone


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        fields = ["id", "name", "countries", "states", "is_active"]
        read_only_fields = ["id"]


class ShippingRateSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ShippingRate
        fields = [
            "id",
            "zone",
            "zone_name",
            "name",
            "min_order_value",
            "max_order_value",
            "price",
            "is_free_above",
            "estimated_days",
            "is_active",
        ]
        read_only_fields = ["id"]


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = [
            "id",
            "order",
            "carrier",
            "tracking_number",
            "tracking_url",
            "status",
            "events",
            "estimated_delivery",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CalculateShippingSerializer(serializers.Serializer):
    """Calculate available shipping rates for a given pincode and order value."""

    pincode = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100, default="India")
    order_value = serializers.DecimalField(max_digits=12, decimal_places=2)
