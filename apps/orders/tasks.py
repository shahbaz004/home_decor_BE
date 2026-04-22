"""
Celery tasks for order-related emails and notifications.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: str):
    """Send order confirmation email to the customer."""
    try:
        from .models import Order
        from apps.core.utils import send_email

        order = Order.objects.prefetch_related("items", "addresses").get(id=order_id)

        context = {
            "order": order,
            "items": list(order.items.all()),
            "shipping_address": order.addresses.filter(type="shipping").first(),
        }

        send_email(
            subject=f"Order Confirmation – {order.order_number}",
            recipient_list=[order.email],
            template_name="order_confirmation",
            context=context,
        )
        logger.info("Order confirmation email sent for order %s", order.order_number)
    except Exception as exc:
        logger.error("Failed to send order confirmation for %s: %s", order_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_status_update_email(self, order_id: str, new_status: str):
    """Notify the customer when their order status changes."""
    try:
        from .models import Order
        from apps.core.utils import send_email

        order = Order.objects.get(id=order_id)

        status_messages = {
            "confirmed": "Your order has been confirmed and is being prepared.",
            "processing": "Your order is currently being processed.",
            "shipped": "Great news! Your order is on its way.",
            "delivered": "Your order has been delivered. Enjoy!",
            "cancelled": "Your order has been cancelled.",
            "refunded": "Your refund has been processed.",
        }

        context = {
            "order": order,
            "status_message": status_messages.get(new_status, f"Your order status is now: {new_status}"),
            "new_status": new_status,
        }

        send_email(
            subject=f"Order Update – {order.order_number}",
            recipient_list=[order.email],
            template_name="order_status_update",
            context=context,
        )
        logger.info("Status update email sent for order %s → %s", order.order_number, new_status)
    except Exception as exc:
        logger.error("Failed to send status update for %s: %s", order_id, exc)
        raise self.retry(exc=exc)
