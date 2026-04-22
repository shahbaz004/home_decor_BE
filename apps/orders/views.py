"""
Order views.
"""

import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.cart.models import Cart, CartItem
from apps.core.exceptions import BusinessLogicError
from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin

from .models import Order, OrderAddress, OrderItem, OrderStatusHistory
from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    UpdateOrderStatusSerializer,
)
from .utils import generate_invoice_pdf

logger = logging.getLogger(__name__)


class OrderViewSet(ModelViewSet):
    """
    Create and manage orders.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items", "addresses", "status_history").select_related("user")
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ("retrieve", "update_status"):
            return OrderDetailSerializer
        return OrderListSerializer

    @transaction.atomic
    def create(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get user cart
        try:
            cart = Cart.objects.prefetch_related("items__product", "items__variant").get(user=request.user)
        except Cart.DoesNotExist:
            raise BusinessLogicError("Your cart is empty.")

        if cart.is_empty:
            raise BusinessLogicError("Your cart is empty.")

        # Validate stock for all items
        for item in cart.items.all():
            available = item.variant.stock if item.variant else item.product.stock
            if available < item.quantity:
                raise BusinessLogicError(
                    f"Insufficient stock for '{item.product.name}'. Only {available} available."
                )

        # Calculate totals
        subtotal = cart.subtotal
        discount = 0
        coupon = None

        coupon_code = data.get("coupon_code", "")
        if coupon_code:
            from apps.coupons.utils import calculate_discount
            from apps.coupons.models import Coupon

            try:
                coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
                discount = calculate_discount(coupon, subtotal)
            except Coupon.DoesNotExist:
                pass

        shipping_cost = 0
        if data.get("shipping_rate_id"):
            from apps.shipping.models import ShippingRate

            try:
                rate = ShippingRate.objects.get(id=data["shipping_rate_id"])
                shipping_cost = rate.price if subtotal < (rate.is_free_above or float("inf")) else 0
            except ShippingRate.DoesNotExist:
                pass

        from django.conf import settings

        tax_rate = getattr(settings, "TAX_RATE", 0.18)
        taxable_amount = subtotal - discount
        tax = round(taxable_amount * tax_rate, 2)
        total = taxable_amount + shipping_cost + tax

        shipping_addr = data["shipping_address_id"]
        billing_addr = (
            data.get("billing_address_id") if not data["use_shipping_as_billing"] else shipping_addr
        )

        # Create the order
        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            subtotal=subtotal,
            discount=discount,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            coupon_code=coupon_code.upper() if coupon_code else "",
            notes=data.get("notes", ""),
        )

        # Snapshot addresses
        def _snapshot_address(addr, addr_type):
            OrderAddress.objects.create(
                order=order,
                type=addr_type,
                full_name=addr.full_name,
                phone=addr.phone,
                street_address=addr.street_address,
                apartment=addr.apartment,
                city=addr.city,
                state=addr.state,
                pincode=addr.pincode,
                country=addr.country,
            )

        _snapshot_address(shipping_addr, OrderAddress.AddressType.SHIPPING)
        _snapshot_address(billing_addr, OrderAddress.AddressType.BILLING)

        # Create order items and deduct stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                product_name=item.product.name,
                variant_name=item.variant.name if item.variant else "",
                sku=item.variant.sku if item.variant else item.product.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            # Deduct stock
            if item.variant:
                item.variant.stock -= item.quantity
                item.variant.save(update_fields=["stock"])
            else:
                item.product.stock -= item.quantity
                item.product.save(update_fields=["stock"])

        # Record initial status
        OrderStatusHistory.objects.create(
            order=order,
            status=Order.Status.PENDING,
            note="Order created.",
            created_by=request.user,
        )

        # Record coupon usage
        if coupon:
            from apps.coupons.models import CouponUsage

            CouponUsage.objects.create(coupon=coupon, user=request.user, order=order)
            coupon.used_count += 1
            coupon.save(update_fields=["used_count"])

        # Clear the cart
        cart.items.all().delete()

        # Send confirmation email asynchronously
        try:
            from apps.orders.tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(str(order.id))
        except Exception:
            logger.warning("Could not dispatch order confirmation email.")

        return Response(
            {
                "success": True,
                "message": "Order placed successfully.",
                "data": OrderDetailSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        return Response({"success": True, "data": OrderDetailSerializer(order).data})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an order (customer action)."""
        order = self.get_object()
        if not order.can_be_cancelled:
            raise BusinessLogicError("This order cannot be cancelled at its current stage.")

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])

        # Restore stock
        for item in order.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save(update_fields=["stock"])
            elif item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=["stock"])

        OrderStatusHistory.objects.create(
            order=order,
            status=Order.Status.CANCELLED,
            note="Order cancelled by customer.",
            created_by=request.user,
        )

        return Response(
            {"success": True, "message": "Order cancelled.", "data": OrderDetailSerializer(order).data}
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        """Update order status (admin action)."""
        order = self.get_object()
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        note = serializer.validated_data.get("note", "")

        order.status = new_status
        order.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            note=note,
            created_by=request.user,
        )

        # Notify customer
        try:
            from apps.orders.tasks import send_status_update_email
            send_status_update_email.delay(str(order.id), new_status)
        except Exception:
            logger.warning("Could not dispatch status update email.")

        return Response(
            {"success": True, "data": OrderDetailSerializer(order).data}
        )

    @action(detail=True, methods=["get"])
    def invoice(self, request, pk=None):
        """Download the order invoice as a PDF."""
        order = self.get_object()
        pdf_content = generate_invoice_pdf(order)
        from django.http import HttpResponse

        response = HttpResponse(pdf_content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="invoice-{order.order_number}.pdf"'
        return response
