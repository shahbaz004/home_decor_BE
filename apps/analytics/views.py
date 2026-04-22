"""
Analytics views – admin dashboard only.
"""

import logging
from datetime import timedelta

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdmin
from apps.orders.models import Order, OrderItem
from apps.products.models import Product

from .models import ProductView, SalesReport
from .serializers import DashboardStatsSerializer, SalesReportSerializer, TopProductSerializer

logger = logging.getLogger(__name__)


def dashboard_callback(request, context):
    """
    Callback used by the Django Unfold admin sidebar to inject dashboard data.
    """
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today).count()
    revenue_today = Order.objects.filter(
        created_at__date=today, is_paid=True
    ).aggregate(total=Sum("total"))["total"] or 0

    context.update(
        {
            "orders_today": orders_today,
            "revenue_today": revenue_today,
        }
    )
    return context


class DashboardStatsView(APIView):
    """Return aggregate statistics for the admin dashboard."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        today = timezone.now().date()

        stats = {
            "total_revenue": Order.objects.filter(is_paid=True).aggregate(
                total=Sum("total")
            )["total"] or 0,
            "total_orders": Order.objects.count(),
            "total_customers": User.objects.filter(is_staff=False).count(),
            "total_products": Product.objects.filter(is_active=True, deleted_at__isnull=True).count(),
            "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
            "revenue_today": Order.objects.filter(
                created_at__date=today, is_paid=True
            ).aggregate(total=Sum("total"))["total"] or 0,
            "orders_today": Order.objects.filter(created_at__date=today).count(),
            "low_stock_count": Product.objects.filter(
                stock__gt=0, stock__lte=5, is_active=True, deleted_at__isnull=True
            ).count(),
        }

        return Response({"success": True, "data": stats})


class SalesChartView(APIView):
    """Return daily revenue data for the past N days."""

    permission_classes = [IsAdmin]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        days = min(days, 365)  # Cap at 1 year
        since = timezone.now() - timedelta(days=days)

        data = (
            Order.objects.filter(created_at__gte=since, is_paid=True)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(revenue=Sum("total"), orders=Count("id"))
            .order_by("date")
        )

        return Response(
            {
                "success": True,
                "data": [
                    {
                        "date": str(row["date"]),
                        "revenue": float(row["revenue"]),
                        "orders": row["orders"],
                    }
                    for row in data
                ],
            }
        )


class TopProductsView(APIView):
    """Return the top-selling products."""

    permission_classes = [IsAdmin]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        limit = min(limit, 50)

        top = (
            OrderItem.objects.values("product__id", "product__name")
            .annotate(
                total_sold=Sum("quantity"),
                total_revenue=Sum("total_price"),
            )
            .order_by("-total_sold")[:limit]
        )

        data = [
            {
                "product_id": str(row["product__id"]),
                "product_name": row["product__name"],
                "total_sold": row["total_sold"],
                "total_revenue": float(row["total_revenue"] or 0),
            }
            for row in top
        ]

        return Response({"success": True, "data": data})


class RecentOrdersView(APIView):
    """Return the most recent orders for the admin dashboard."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.orders.serializers import OrderListSerializer

        limit = int(request.query_params.get("limit", 10))
        orders = Order.objects.select_related("user").order_by("-created_at")[:limit]
        serializer = OrderListSerializer(orders, many=True)
        return Response({"success": True, "data": serializer.data})
