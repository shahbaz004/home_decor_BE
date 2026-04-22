from django.urls import path

from .views import DashboardStatsView, RecentOrdersView, SalesChartView, TopProductsView

app_name = "analytics"

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="dashboard_stats"),
    path("sales-chart/", SalesChartView.as_view(), name="sales_chart"),
    path("top-products/", TopProductsView.as_view(), name="top_products"),
    path("recent-orders/", RecentOrdersView.as_view(), name="recent_orders"),
]
