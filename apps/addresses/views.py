"""
CRUD views for user addresses.
"""

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Address
from .serializers import AddressSerializer


class AddressViewSet(ModelViewSet):
    """CRUD for the authenticated user's addresses."""

    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by("-is_default", "-created_at")

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You do not own this address.")
        return obj

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default:
            return Response(
                {"success": False, "message": "Cannot delete a default address. Set another address as default first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response({"success": True, "message": "Address deleted."}, status=status.HTTP_200_OK)
