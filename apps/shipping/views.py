"""
Shipping views.
"""

from django.db import models
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdmin

from .models import ShipmentTracking, ShippingRate, ShippingZone
from .serializers import (
    CalculateShippingSerializer,
    ShipmentTrackingSerializer,
    ShippingRateSerializer,
    ShippingZoneSerializer,
)


class ShippingZoneViewSet(ModelViewSet):
    """CRUD for shipping zones (admin only)."""

    queryset = ShippingZone.objects.prefetch_related("rates").filter(is_active=True)
    serializer_class = ShippingZoneSerializer
    permission_classes = [IsAdmin]


class ShippingRateViewSet(ModelViewSet):
    """CRUD for shipping rates (admin only)."""

    queryset = ShippingRate.objects.select_related("zone").filter(is_active=True)
    serializer_class = ShippingRateSerializer
    permission_classes = [IsAdmin]


class CalculateShippingView(APIView):
    """Return applicable shipping rates for a given order value and location."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CalculateShippingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        country = data["country"]
        order_value = data["order_value"]

        rates = ShippingRate.objects.select_related("zone").filter(
            is_active=True,
            zone__is_active=True,
            min_order_value__lte=order_value,
        ).filter(
            models.Q(max_order_value__isnull=True) | models.Q(max_order_value__gte=order_value)
        )

        result = []
        for rate in rates:
            effective_price = rate.get_price_for_order(order_value)
            result.append(
                {
                    "id": str(rate.id),
                    "name": rate.name,
                    "carrier": rate.zone.name,
                    "price": effective_price,
                    "estimated_days": rate.estimated_days,
                    "is_free": effective_price == 0,
                }
            )

        return Response({"success": True, "data": result})


class ShipmentTrackingView(APIView):
    """Get tracking details for an order."""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            tracking = ShipmentTracking.objects.get(order__id=order_id, order__user=request.user)
        except ShipmentTracking.DoesNotExist:
            return Response(
                {"success": False, "message": "Tracking information not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ShipmentTrackingSerializer(tracking)
        return Response({"success": True, "data": serializer.data})
