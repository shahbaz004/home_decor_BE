"""
Custom allauth adapters.
"""

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """Override allauth adapter to use our custom email utilities."""

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Return the frontend URL for email confirmation."""
        key = emailconfirmation.key
        return f"{settings.FRONTEND_URL}/verify-email/{key}/"

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """Send confirmation email via our custom sender."""
        from apps.core.utils import send_email
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = emailconfirmation.email_address.user
        url = self.get_email_confirmation_url(request, emailconfirmation)

        send_email(
            subject="Verify your email – Home Decor",
            recipient_list=[emailconfirmation.email_address.email],
            template_name="account/email/email_confirmation",
            context={
                "user": user,
                "activate_url": url,
            },
        )

    def is_open_for_signup(self, request):
        return True
