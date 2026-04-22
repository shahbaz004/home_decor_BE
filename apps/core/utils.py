"""
Shared utility functions for the home_decor project.
"""

import io
import logging
import random
import string
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from PIL import Image

logger = logging.getLogger(__name__)


def generate_order_number() -> str:
    """
    Generate a unique, human-readable order number.
    Format: HD-YYYYMMDD-XXXXXX  (HD = Home Decor, then date, then 6 random chars)
    """
    date_part = timezone.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"HD-{date_part}-{random_part}"


def send_email(
    subject: str,
    recipient_list: list[str],
    template_name: str,
    context: dict,
    from_email: Optional[str] = None,
    attachments: Optional[list] = None,
) -> bool:
    """
    Send a templated HTML email with a plain-text fallback.

    Parameters
    ----------
    subject:       Email subject line.
    recipient_list: List of recipient email addresses.
    template_name: Base template name (without extension).
                   The function looks for ``<template_name>.html`` and
                   ``<template_name>.txt``.
    context:       Template rendering context.
    from_email:    Sender address; falls back to DEFAULT_FROM_EMAIL.
    attachments:   Optional list of ``(filename, content, mimetype)`` tuples.

    Returns
    -------
    True if the email was dispatched successfully, False otherwise.
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    context.setdefault("site_name", "Home Decor")
    context.setdefault("frontend_url", settings.FRONTEND_URL)

    try:
        html_body = render_to_string(f"emails/{template_name}.html", context)
        text_body = render_to_string(f"emails/{template_name}.txt", context)
    except Exception:
        # Fallback: use subject as plain-text body if templates are missing.
        html_body = f"<p>{subject}</p>"
        text_body = subject

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=recipient_list,
    )
    msg.attach_alternative(html_body, "text/html")

    if attachments:
        for filename, content, mimetype in attachments:
            msg.attach(filename, content, mimetype)

    try:
        msg.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", recipient_list, exc)
        return False


def compress_image(
    image_field,
    max_width: int = 1200,
    max_height: int = 1200,
    quality: int = 85,
    output_format: str = "WEBP",
) -> io.BytesIO:
    """
    Compress and resize an uploaded image in-memory.

    Parameters
    ----------
    image_field:   A Django ``InMemoryUploadedFile`` or ``FieldFile``.
    max_width:     Maximum output width in pixels.
    max_height:    Maximum output height in pixels.
    quality:       JPEG/WebP compression quality (1–95).
    output_format: Pillow format string ("JPEG", "WEBP", "PNG").

    Returns
    -------
    BytesIO buffer containing the compressed image data.
    """
    img = Image.open(image_field)

    # Convert palette / transparency modes to RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA" if output_format == "PNG" else "RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize while preserving aspect ratio
    img.thumbnail((max_width, max_height), Image.LANCZOS)

    output = io.BytesIO()
    save_kwargs: dict = {"format": output_format, "optimize": True}
    if output_format in ("JPEG", "WEBP"):
        save_kwargs["quality"] = quality

    img.save(output, **save_kwargs)
    output.seek(0)
    return output


def generate_slug_from_name(name: str) -> str:
    """
    Naively slugify a name. For production use prefer
    ``django.utils.text.slugify``.
    """
    from django.utils.text import slugify

    return slugify(name)


def mask_email(email: str) -> str:
    """Return a partially masked email for display purposes."""
    local, _, domain = email.partition("@")
    visible = local[:2] if len(local) > 2 else local[0]
    masked_local = visible + "*" * (len(local) - len(visible))
    return f"{masked_local}@{domain}"
