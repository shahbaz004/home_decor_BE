from rest_framework import serializers

from .models import ProductView, SalesReport


class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = ["date", "total_orders", "total_revenue", "total_items", "new_customers"]


class DashboardStatsSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_products = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=14, decimal_places=2)
    orders_today = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()


class TopProductSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
