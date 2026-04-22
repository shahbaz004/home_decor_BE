"""
Serializers for the cart app.
"""

from rest_framework import serializers

from apps.products.serializers import ProductListSerializer, ProductVariantSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source="product", read_only=True)
    variant_detail = ProductVariantSerializer(source="variant", read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_detail",
            "variant",
            "variant_detail",
            "quantity",
            "unit_price",
            "total_price",
        ]
        read_only_fields = ["id", "unit_price"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "total_items", "subtotal", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AddToCartSerializer(serializers.Serializer):
    """Validates add-to-cart requests."""

    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        from apps.products.models import Product, ProductVariant

        try:
            product = Product.objects.get(id=attrs["product_id"], is_active=True, deleted_at__isnull=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found or unavailable."})

        variant = None
        if attrs.get("variant_id"):
            try:
                variant = ProductVariant.objects.get(id=attrs["variant_id"], product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError({"variant_id": "Variant not found or unavailable."})

        available_stock = variant.stock if variant else product.stock
        if available_stock < attrs["quantity"]:
            raise serializers.ValidationError(
                {"quantity": f"Only {available_stock} units available."}
            )

        attrs["product"] = product
        attrs["variant"] = variant
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
