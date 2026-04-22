from django.urls import path

from .views import (
    CreateRazorpayOrderView,
    CreateStripePaymentIntentView,
    RazorpayWebhookView,
    StripeWebhookView,
    VerifyRazorpayPaymentView,
)

app_name = "payments"

urlpatterns = [
    path("razorpay/create/", CreateRazorpayOrderView.as_view(), name="razorpay_create"),
    path("razorpay/verify/", VerifyRazorpayPaymentView.as_view(), name="razorpay_verify"),
    path("razorpay/webhook/", RazorpayWebhookView.as_view(), name="razorpay_webhook"),
    path("stripe/create-intent/", CreateStripePaymentIntentView.as_view(), name="stripe_create_intent"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe_webhook"),
]
