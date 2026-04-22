"""
Payment serializers.
"""

from rest_framework import serializers

from .models import Payment, Refund


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "provider",
            "amount",
            "currency",
            "status",
            "provider_payment_id",
            "provider_order_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PaymentCreateSerializer(serializers.Serializer):
    """Initiate a payment for an order."""

    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=Payment.Provider.choices)

    def validate_order_id(self, value):
        from apps.orders.models import Order

        try:
            order = Order.objects.get(id=value, user=self.context["request"].user)
            if order.is_paid:
                raise serializers.ValidationError("This order is already paid.")
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")


class PaymentVerifySerializer(serializers.Serializer):
    """Verify a Razorpay payment."""

    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class StripePaymentIntentSerializer(serializers.Serializer):
    """Create a Stripe PaymentIntent."""

    order_id = serializers.UUIDField()

    def validate_order_id(self, value):
        from apps.orders.models import Order

        try:
            order = Order.objects.get(id=value, user=self.context["request"].user)
            if order.is_paid:
                raise serializers.ValidationError("This order is already paid.")
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ["id", "payment", "amount", "reason", "status", "provider_refund_id", "created_at"]
        read_only_fields = ["id", "status", "provider_refund_id", "created_at"]
