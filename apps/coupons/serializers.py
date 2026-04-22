from rest_framework import serializers

from .models import Coupon, CouponUsage
from .utils import calculate_discount


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "description",
            "type",
            "value",
            "min_order_value",
            "max_discount",
            "usage_limit",
            "usage_limit_per_user",
            "used_count",
            "valid_from",
            "valid_to",
            "is_active",
            "is_valid",
            "applicable_categories",
            "applicable_products",
            "created_at",
        ]
        read_only_fields = ["id", "used_count", "created_at"]

    def validate_code(self, value: str) -> str:
        return value.upper().strip()


class ApplyCouponSerializer(serializers.Serializer):
    """Validate a coupon against the current cart."""

    code = serializers.CharField()
    order_value = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate(self, attrs):
        code = attrs["code"].upper().strip()
        order_value = attrs["order_value"]

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"code": "Coupon code not found."})

        user = self.context["request"].user
        if user.is_authenticated:
            if not coupon.is_valid_for_user(user):
                raise serializers.ValidationError({"code": "This coupon is no longer valid or you have already used it."})
        else:
            if not coupon.is_valid:
                raise serializers.ValidationError({"code": "This coupon is no longer valid."})

        if order_value < coupon.min_order_value:
            raise serializers.ValidationError(
                {"code": f"Minimum order value for this coupon is ₹{coupon.min_order_value}."}
            )

        discount = calculate_discount(coupon, order_value)

        attrs["coupon"] = coupon
        attrs["discount"] = discount
        return attrs


class CouponUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponUsage
        fields = ["id", "coupon", "user", "order", "discount_amount", "created_at"]
        read_only_fields = ["id", "created_at"]
