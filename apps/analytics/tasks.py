"""
Analytics Celery tasks.
"""

import logging
from datetime import date, timedelta

from celery import shared_task
from django.db.models import Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def record_product_view(product_id: str, user_id: str | None, session_key: str, ip_address: str):
    """Record a single product page view asynchronously."""
    try:
        from apps.products.models import Product
        from .models import ProductView

        product = Product.objects.get(id=product_id)

        user = None
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        ProductView.objects.create(
            product=product,
            user=user,
            session_key=session_key or "",
            ip_address=ip_address or None,
        )
    except Exception as exc:
        logger.warning("Failed to record product view for %s: %s", product_id, exc)


@shared_task
def generate_daily_sales_report():
    """
    Aggregate yesterday's orders into a SalesReport row.
    Should be scheduled to run daily at midnight.
    """
    from apps.orders.models import Order
    from django.contrib.auth import get_user_model
    from .models import SalesReport

    User = get_user_model()
    yesterday = timezone.now().date() - timedelta(days=1)

    orders_qs = Order.objects.filter(created_at__date=yesterday, is_paid=True)

    total_orders = orders_qs.count()
    total_revenue = orders_qs.aggregate(total=Sum("total"))["total"] or 0
    total_items = sum(
        order.items.aggregate(qty=Sum("quantity"))["qty"] or 0 for order in orders_qs
    )
    new_customers = User.objects.filter(date_joined__date=yesterday).count()

    report, created = SalesReport.objects.update_or_create(
        date=yesterday,
        defaults={
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_items": total_items,
            "new_customers": new_customers,
        },
    )

    logger.info(
        "Sales report for %s: orders=%d, revenue=%s, items=%d",
        yesterday, total_orders, total_revenue, total_items,
    )
    return str(report.id)
