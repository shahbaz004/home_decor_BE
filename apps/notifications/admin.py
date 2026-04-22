from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import EmailLog, Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ["user", "type", "title", "is_read", "created_at"]
    list_filter = ["type", "is_read"]
    search_fields = ["user__email", "title", "message"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = ["to", "subject", "template", "status", "sent_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["to", "subject"]
    readonly_fields = ["id", "created_at", "updated_at", "sent_at"]
