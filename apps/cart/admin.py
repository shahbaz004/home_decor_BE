from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    fields = ["product", "variant", "quantity", "unit_price"]
    readonly_fields = ["unit_price"]


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ["id", "user", "session_key", "total_items", "subtotal", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email", "session_key"]
    inlines = [CartItemInline]
    readonly_fields = ["id", "created_at", "updated_at"]
