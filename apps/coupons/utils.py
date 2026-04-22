"""
Coupon discount calculation utilities.
"""

from decimal import Decimal


def calculate_discount(coupon, order_subtotal: Decimal) -> Decimal:
    """
    Calculate the discount amount for a given coupon and order subtotal.

    Parameters
    ----------
    coupon:         A ``Coupon`` model instance.
    order_subtotal: The order subtotal (before discount) as a Decimal.

    Returns
    -------
    Decimal discount amount (capped at order subtotal).
    """
    if not coupon.is_valid:
        return Decimal("0")

    if order_subtotal < coupon.min_order_value:
        return Decimal("0")

    if coupon.type == "percentage":
        discount = order_subtotal * (coupon.value / Decimal("100"))
        if coupon.max_discount is not None:
            discount = min(discount, coupon.max_discount)

    elif coupon.type == "fixed":
        discount = coupon.value

    elif coupon.type == "free_shipping":
        # Shipping-only discount; handled separately in order creation.
        return Decimal("0")

    else:
        return Decimal("0")

    return min(discount, order_subtotal)
