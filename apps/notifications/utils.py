"""
Notification utility functions.
"""

import logging

from django.contrib.auth import get_user_model

from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


def create_notification(
    user,
    title: str,
    message: str,
    notification_type: str = Notification.NotificationType.SYSTEM,
    action_url: str = "",
    data: dict = None,
) -> Notification:
    """
    Create an in-app notification for a user.

    Parameters
    ----------
    user:              The recipient user (model instance or PK).
    title:             Short notification title.
    message:           Full notification message.
    notification_type: One of Notification.NotificationType values.
    action_url:        Optional deep link for the notification.
    data:              Optional JSON payload.

    Returns
    -------
    The created Notification instance.
    """
    if data is None:
        data = {}

    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        action_url=action_url,
        data=data,
    )
    return notification


def create_order_notification(user, order) -> Notification:
    return create_notification(
        user=user,
        title=f"Order {order.order_number} confirmed",
        message=f"Your order {order.order_number} has been placed successfully.",
        notification_type=Notification.NotificationType.ORDER,
        action_url=f"/orders/{order.id}/",
        data={"order_id": str(order.id), "order_number": order.order_number},
    )


def create_shipping_notification(user, order, tracking_number: str) -> Notification:
    return create_notification(
        user=user,
        title="Your order has shipped!",
        message=f"Order {order.order_number} is on its way. Tracking: {tracking_number}",
        notification_type=Notification.NotificationType.SHIPPING,
        action_url=f"/orders/{order.id}/tracking/",
        data={"order_id": str(order.id), "tracking_number": tracking_number},
    )
