from rest_framework import serializers

from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ["id", "image"]
        read_only_fields = ["id"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "user",
            "user_name",
            "rating",
            "title",
            "body",
            "is_verified_purchase",
            "is_approved",
            "images",
            "created_at",
        ]
        read_only_fields = ["id", "user", "is_verified_purchase", "is_approved", "created_at"]

    def get_user_name(self, obj) -> str:
        return obj.user.get_short_name() or obj.user.email.split("@")[0]

    def validate(self, attrs):
        request = self.context["request"]
        product = attrs.get("product")

        # Prevent duplicate reviews
        if product and Review.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError("You have already reviewed this product.")

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReviewCreateSerializer(serializers.ModelSerializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Review
        fields = ["product", "rating", "title", "body", "uploaded_images"]

    def validate(self, attrs):
        request = self.context["request"]
        product = attrs.get("product")
        if product and Review.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        return attrs

    def create(self, validated_data):
        images = validated_data.pop("uploaded_images", [])
        validated_data["user"] = self.context["request"].user
        review = Review.objects.create(**validated_data)
        for img in images:
            ReviewImage.objects.create(review=review, image=img)
        return review
