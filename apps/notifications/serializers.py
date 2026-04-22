from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "is_read",
            "action_url",
            "data",
            "created_at",
        ]
        read_only_fields = ["id", "type", "title", "message", "action_url", "data", "created_at"]
