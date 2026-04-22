from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Address


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ["full_name", "user", "type", "city", "state", "country", "is_default"]
    list_filter = ["type", "country", "is_default"]
    search_fields = ["full_name", "user__email", "city", "state", "pincode"]
    raw_id_fields = ["user"]
    readonly_fields = ["id", "created_at", "updated_at"]
