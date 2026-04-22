from rest_framework import serializers

from apps.products.serializers import ProductListSerializer, ProductVariantSerializer

from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source="product", read_only=True)
    variant_detail = ProductVariantSerializer(source="variant", read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_detail", "variant", "variant_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        product = attrs["product"]
        variant = attrs.get("variant")
        if WishlistItem.objects.filter(user=user, product=product, variant=variant).exists():
            raise serializers.ValidationError("This product is already in your wishlist.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class MoveToCartSerializer(serializers.Serializer):
    wishlist_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
