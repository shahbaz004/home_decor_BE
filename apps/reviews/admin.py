from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Review, ReviewImage


class ReviewImageInline(TabularInline):
    model = ReviewImage
    extra = 0
    fields = ["image"]


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = [
        "product",
        "user",
        "rating",
        "title",
        "is_verified_purchase",
        "is_approved",
        "created_at",
    ]
    list_filter = ["rating", "is_approved", "is_verified_purchase"]
    search_fields = ["product__name", "user__email", "title"]
    readonly_fields = ["id", "is_verified_purchase", "created_at", "updated_at"]
    actions = ["approve_reviews", "reject_reviews"]
    inlines = [ReviewImageInline]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
