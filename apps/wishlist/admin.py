from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(ModelAdmin):
    list_display = ["user", "product", "variant", "created_at"]
    search_fields = ["user__email", "product__name"]
    raw_id_fields = ["user", "product", "variant"]
    readonly_fields = ["id", "created_at", "updated_at"]
