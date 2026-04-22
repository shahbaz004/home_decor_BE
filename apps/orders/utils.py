"""
Order utilities – PDF invoice generation.
"""

import logging

from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def generate_invoice_pdf(order) -> bytes:
    """
    Render an order as an HTML template and convert to PDF using WeasyPrint.

    Returns the raw PDF bytes which can be streamed in an HTTP response or
    attached to an email.
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        logger.error("WeasyPrint is not installed. Cannot generate PDF.")
        raise

    context = {
        "order": order,
        "items": order.items.all(),
        "shipping_address": order.addresses.filter(type="shipping").first(),
        "billing_address": order.addresses.filter(type="billing").first(),
        "site_name": "Home Decor",
        "currency_symbol": getattr(settings, "CURRENCY_SYMBOL", "₹"),
    }

    html_string = render_to_string("orders/invoice.html", context)
    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    pdf = HTML(string=html_string, base_url=base_url).write_pdf()
    return pdf
