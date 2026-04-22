"""
Celery tasks for sending emails and notifications.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(self, to: str, subject: str, template_name: str, context: dict):
    """
    Generic email sender task.
    Logs the outcome in EmailLog.
    """
    from apps.core.utils import send_email
    from .models import EmailLog

    log = EmailLog.objects.create(to=to, subject=subject, template=template_name)

    try:
        success = send_email(
            subject=subject,
            recipient_list=[to],
            template_name=template_name,
            context=context,
        )
        if success:
            log.status = EmailLog.EmailStatus.SENT
            log.sent_at = timezone.now()
        else:
            log.status = EmailLog.EmailStatus.FAILED
            log.error_message = "send_email returned False."
        log.save(update_fields=["status", "sent_at", "error_message"])
    except Exception as exc:
        log.status = EmailLog.EmailStatus.FAILED
        log.error_message = str(exc)
        log.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email(self, user_id: str):
    """Send a welcome email to a newly registered user."""
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(id=user_id)

        send_email_task.delay(
            to=user.email,
            subject="Welcome to Home Decor!",
            template_name="welcome",
            context={
                "user": {"first_name": user.first_name or user.email.split("@")[0]},
                "email": user.email,
            },
        )
    except Exception as exc:
        logger.error("Failed to send welcome email to user %s: %s", user_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_order_confirmation(self, order_id: str):
    """Send an order confirmation email."""
    try:
        from apps.orders.models import Order

        order = Order.objects.prefetch_related("items", "addresses").get(id=order_id)

        send_email_task.delay(
            to=order.email,
            subject=f"Your Order {order.order_number} is Confirmed!",
            template_name="order_confirmation",
            context={
                "order_number": order.order_number,
                "total": str(order.total),
                "items_count": order.items.count(),
            },
        )
    except Exception as exc:
        logger.error("Failed to send order confirmation for %s: %s", order_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset(self, user_id: str, reset_url: str):
    """Send a password-reset email."""
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(id=user_id)

        send_email_task.delay(
            to=user.email,
            subject="Reset Your Password – Home Decor",
            template_name="password_reset",
            context={
                "user": {"first_name": user.first_name or user.email.split("@")[0]},
                "reset_url": reset_url,
                "expiry_hours": 24,
            },
        )
    except Exception as exc:
        logger.error("Failed to send password reset for user %s: %s", user_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_abandoned_cart_email(self, user_id: str):
    """
    Send an abandoned-cart reminder if the user still has unpurchased cart items.
    This task is intended to be called ~1 hour after the cart was last modified.
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.cart.models import Cart

        User = get_user_model()
        user = User.objects.get(id=user_id)

        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return  # Cart was purchased or cleared

        if cart.is_empty:
            return

        send_email_task.delay(
            to=user.email,
            subject="You left something behind! 🛒",
            template_name="abandoned_cart",
            context={
                "user": {"first_name": user.first_name or user.email.split("@")[0]},
                "cart_url": f"{__import__('django').conf.settings.FRONTEND_URL}/cart",
                "items_count": cart.total_items,
            },
        )
    except Exception as exc:
        logger.error("Failed to send abandoned cart email for user %s: %s", user_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_sms_task(self, phone: str, message: str):
    """
    Send an SMS notification.
    Placeholder – integrate with your SMS provider (e.g. Twilio, MSG91).
    """
    logger.info("SMS to %s: %s", phone, message)
    # TODO: integrate with SMS provider
