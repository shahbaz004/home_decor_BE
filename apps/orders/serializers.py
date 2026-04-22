"""
Order serializers.
"""

from rest_framework import serializers

from .models import Order, OrderAddress, OrderItem, OrderStatusHistory


class OrderAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAddress
        fields = [
            "type",
            "full_name",
            "phone",
            "street_address",
            "apartment",
            "city",
            "state",
            "pincode",
            "country",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "variant",
            "product_name",
            "variant_name",
            "sku",
            "quantity",
            "unit_price",
            "total_price",
        ]
        read_only_fields = ["id", "total_price"]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ["status", "note", "created_by_email", "created_at"]


class OrderListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "subtotal",
            "discount",
            "shipping_cost",
            "tax",
            "total",
            "is_paid",
            "item_count",
            "created_at",
        ]

    def get_item_count(self, obj) -> int:
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    addresses = OrderAddressSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "email",
            "status",
            "subtotal",
            "discount",
            "shipping_cost",
            "tax",
            "total",
            "coupon_code",
            "notes",
            "is_paid",
            "items",
            "addresses",
            "status_history",
            "can_be_cancelled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_number", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.Serializer):
    """Create an order from the current cart."""

    shipping_address_id = serializers.UUIDField()
    billing_address_id = serializers.UUIDField(required=False)
    use_shipping_as_billing = serializers.BooleanField(default=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    shipping_rate_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_shipping_address_id(self, value):
        from apps.addresses.models import Address

        try:
            return Address.objects.get(id=value, user=self.context["request"].user)
        except Address.DoesNotExist:
            raise serializers.ValidationError("Shipping address not found.")

    def validate_billing_address_id(self, value):
        if not value:
            return None
        from apps.addresses.models import Address

        try:
            return Address.objects.get(id=value, user=self.context["request"].user)
        except Address.DoesNotExist:
            raise serializers.ValidationError("Billing address not found.")


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True)
