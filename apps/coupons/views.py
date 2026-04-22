"""
Coupon views – validation and admin CRUD.
"""

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdmin

from .models import Coupon
from .serializers import ApplyCouponSerializer, CouponSerializer


class ValidateCouponView(APIView):
    """Validate a coupon code and return the applicable discount."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ApplyCouponSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        coupon = data["coupon"]
        return Response(
            {
                "success": True,
                "data": {
                    "code": coupon.code,
                    "type": coupon.type,
                    "value": coupon.value,
                    "discount": data["discount"],
                    "description": coupon.description,
                },
            }
        )


class CouponViewSet(ModelViewSet):
    """Admin CRUD for coupons."""

    queryset = Coupon.objects.prefetch_related("applicable_categories", "applicable_products")
    serializer_class = CouponSerializer
    permission_classes = [IsAdmin]
    search_fields = ["code", "description"]
    filterset_fields = ["is_active", "type"]
    ordering = ["-created_at"]
