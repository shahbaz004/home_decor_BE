"""
Notification views.
"""

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.pagination import StandardPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(ReadOnlyModelViewSet):
    """List and manage in-app notifications for the authenticated user."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filterset_fields = ["is_read", "type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"success": True, "message": "Marked as read."})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"success": True, "message": f"{count} notifications marked as read."})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"success": True, "data": {"count": count}})
