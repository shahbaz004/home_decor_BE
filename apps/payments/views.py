"""
Payment gateway views.
"""

import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order, OrderStatusHistory

from .models import Payment, Refund
from .serializers import (
    PaymentCreateSerializer,
    PaymentVerifySerializer,
    RefundSerializer,
    StripePaymentIntentSerializer,
)

logger = logging.getLogger(__name__)


class CreateRazorpayOrderView(APIView):
    """Create a Razorpay order and return the order ID."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data["order_id"]

        import razorpay

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        amount_in_paise = int(order.total * 100)
        try:
            rz_order = client.order.create(
                {
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "receipt": str(order.id),
                    "notes": {"order_number": order.order_number},
                }
            )
        except Exception as exc:
            logger.error("Razorpay order creation failed: %s", exc)
            return Response(
                {"success": False, "message": "Payment gateway error. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        Payment.objects.create(
            order=order,
            provider=Payment.Provider.RAZORPAY,
            amount=order.total,
            currency="INR",
            provider_order_id=rz_order["id"],
            raw_response=rz_order,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "razorpay_order_id": rz_order["id"],
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "key": settings.RAZORPAY_KEY_ID,
                    "order_number": order.order_number,
                },
            }
        )


class VerifyRazorpayPaymentView(APIView):
    """Verify the Razorpay payment signature and mark order as paid."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Verify signature
        expected = hmac.new(
            key=settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            msg=f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, data["razorpay_signature"]):
            return Response(
                {"success": False, "message": "Invalid payment signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(provider_order_id=data["razorpay_order_id"])
        except Payment.DoesNotExist:
            return Response(
                {"success": False, "message": "Payment record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment.status = Payment.Status.CAPTURED
        payment.provider_payment_id = data["razorpay_payment_id"]
        payment.provider_signature = data["razorpay_signature"]
        payment.save(update_fields=["status", "provider_payment_id", "provider_signature"])

        order = payment.order
        order.is_paid = True
        order.status = Order.Status.CONFIRMED
        order.save(update_fields=["is_paid", "status"])

        OrderStatusHistory.objects.create(
            order=order,
            status=Order.Status.CONFIRMED,
            note=f"Payment received via Razorpay. Payment ID: {data['razorpay_payment_id']}",
        )

        return Response({"success": True, "message": "Payment verified and order confirmed."})


class CreateStripePaymentIntentView(APIView):
    """Create a Stripe PaymentIntent and return the client secret."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StripePaymentIntentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data["order_id"]

        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY

        amount_in_cents = int(order.total * 100)
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency="inr",
                metadata={"order_id": str(order.id), "order_number": order.order_number},
            )
        except stripe.error.StripeError as exc:
            logger.error("Stripe PaymentIntent creation failed: %s", exc)
            return Response(
                {"success": False, "message": "Payment gateway error. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        Payment.objects.create(
            order=order,
            provider=Payment.Provider.STRIPE,
            amount=order.total,
            currency="INR",
            provider_order_id=intent["id"],
            raw_response=intent,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "client_secret": intent["client_secret"],
                    "payment_intent_id": intent["id"],
                },
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """Handle Stripe webhook events."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        payload = request.body

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            logger.warning("Stripe webhook signature verification failed: %s", exc)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event_type = event["type"]

        if event_type == "payment_intent.succeeded":
            intent = event["data"]["object"]
            self._handle_payment_success(intent)
        elif event_type == "payment_intent.payment_failed":
            intent = event["data"]["object"]
            self._handle_payment_failure(intent)

        return Response({"status": "ok"})

    def _handle_payment_success(self, intent):
        try:
            payment = Payment.objects.get(provider_order_id=intent["id"])
            payment.status = Payment.Status.CAPTURED
            payment.provider_payment_id = intent.get("latest_charge", "")
            payment.save(update_fields=["status", "provider_payment_id"])

            order = payment.order
            order.is_paid = True
            order.status = Order.Status.CONFIRMED
            order.save(update_fields=["is_paid", "status"])

            OrderStatusHistory.objects.create(
                order=order,
                status=Order.Status.CONFIRMED,
                note=f"Stripe payment succeeded. Intent: {intent['id']}",
            )
        except Payment.DoesNotExist:
            logger.warning("No payment found for Stripe intent %s", intent["id"])

    def _handle_payment_failure(self, intent):
        try:
            payment = Payment.objects.get(provider_order_id=intent["id"])
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
        except Payment.DoesNotExist:
            pass


@method_decorator(csrf_exempt, name="dispatch")
class RazorpayWebhookView(APIView):
    """Handle Razorpay webhook events."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")

        expected = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event_type = event.get("event")

        if event_type == "payment.captured":
            payment_entity = event["payload"]["payment"]["entity"]
            self._handle_payment_captured(payment_entity)
        elif event_type == "refund.processed":
            refund_entity = event["payload"]["refund"]["entity"]
            self._handle_refund_processed(refund_entity)

        return Response({"status": "ok"})

    def _handle_payment_captured(self, payment_entity):
        try:
            payment = Payment.objects.get(provider_order_id=payment_entity.get("order_id"))
            payment.status = Payment.Status.CAPTURED
            payment.provider_payment_id = payment_entity.get("id", "")
            payment.save(update_fields=["status", "provider_payment_id"])
        except Payment.DoesNotExist:
            pass

    def _handle_refund_processed(self, refund_entity):
        try:
            payment = Payment.objects.get(provider_payment_id=refund_entity.get("payment_id"))
            Refund.objects.filter(
                payment=payment, provider_refund_id=refund_entity.get("id")
            ).update(status=Refund.Status.PROCESSED)
        except Payment.DoesNotExist:
            pass
