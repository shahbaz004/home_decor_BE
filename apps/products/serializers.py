"""
Serializers for the products app.
"""

from rest_framework import serializers

from .models import (
    Category,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    Tag,
)


class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Flat category serializer — used for children to avoid infinite recursion."""

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "image", "display_order", "product_count"]
        read_only_fields = ["id"]

    def get_product_count(self, obj) -> int:
        return obj.products.filter(is_active=True, deleted_at__isnull=True).count()


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "image",
            "description",
            "is_active",
            "meta_title",
            "meta_description",
            "display_order",
            "children",
            "product_count",
        ]
        read_only_fields = ["id"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategoryMinimalSerializer(children, many=True, context=self.context).data

    def get_product_count(self, obj) -> int:
        return obj.products.filter(is_active=True, deleted_at__isnull=True).count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "display_order"]
        read_only_fields = ["id"]


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "price_adjustment",
            "effective_price",
            "stock",
            "attributes",
            "is_active",
        ]
        read_only_fields = ["id"]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    primary_image = serializers.SerializerMethodField()
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "category",
            "category_name",
            "base_price",
            "sale_price",
            "effective_price",
            "discount_percentage",
            "stock",
            "is_in_stock",
            "is_active",
            "is_featured",
            "primary_image",
            "tags",
            "created_at",
        ]

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image:
            return ProductImageSerializer(image, context=self.context).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail view."""

    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "short_description",
            "category",
            "tags",
            "base_price",
            "sale_price",
            "cost_price",
            "effective_price",
            "discount_percentage",
            "stock",
            "is_in_stock",
            "is_low_stock",
            "is_active",
            "is_featured",
            "is_digital",
            "weight",
            "dimensions",
            "meta_title",
            "meta_description",
            "images",
            "variants",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        ]

    def get_average_rating(self, obj) -> float | None:
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(r.rating for r in reviews)
            return round(total / reviews.count(), 1)
        return None

    def get_review_count(self, obj) -> int:
        return obj.reviews.filter(is_approved=True).count()


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products (admin use)."""

    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), source="tags", required=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "short_description",
            "category",
            "tag_ids",
            "base_price",
            "sale_price",
            "cost_price",
            "stock",
            "low_stock_threshold",
            "is_active",
            "is_featured",
            "is_digital",
            "weight",
            "dimensions",
            "meta_title",
            "meta_description",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        sale_price = attrs.get("sale_price")
        base_price = attrs.get("base_price", getattr(self.instance, "base_price", None))
        if sale_price is not None and base_price is not None and sale_price >= base_price:
            raise serializers.ValidationError(
                {"sale_price": "Sale price must be less than the base price."}
            )
        return attrs
