"""
Cart views – get/create cart, add/update/remove items, merge on login.
"""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import (
    AddToCartSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)

logger = logging.getLogger(__name__)


def get_or_create_cart(request) -> Cart:
    """Return the cart for the current user or session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    # Anonymous user – use session key
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
    return cart


class CartView(APIView):
    """Retrieve the current cart (creates one if none exists)."""

    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart, context={"request": request})
        return Response({"success": True, "data": serializer.data})


class CartItemView(APIView):
    """Add, update or remove items in the cart."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Add an item to the cart."""
        serializer = AddToCartSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart = get_or_create_cart(request)
        product = data["product"]
        variant = data.get("variant")
        quantity = data["quantity"]

        unit_price = variant.effective_price if variant else product.effective_price

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={"quantity": quantity, "unit_price": unit_price},
        )
        if not created:
            new_quantity = item.quantity + quantity
            available = variant.stock if variant else product.stock
            if new_quantity > available:
                return Response(
                    {"success": False, "message": f"Only {available} units available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.quantity = new_quantity
            item.save(update_fields=["quantity", "updated_at"])

        cart_serializer = CartSerializer(cart, context={"request": request})
        return Response(
            {"success": True, "message": "Item added to cart.", "data": cart_serializer.data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request, item_id):
        """Update the quantity of a cart item."""
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = get_or_create_cart(request)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {"success": False, "message": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_qty = serializer.validated_data["quantity"]
        available = item.variant.stock if item.variant else item.product.stock
        if new_qty > available:
            return Response(
                {"success": False, "message": f"Only {available} units available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = new_qty
        item.save(update_fields=["quantity", "updated_at"])

        return Response(
            {"success": True, "data": CartSerializer(cart, context={"request": request}).data}
        )

    def delete(self, request, item_id):
        """Remove an item from the cart."""
        cart = get_or_create_cart(request)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {"success": False, "message": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        return Response(
            {"success": True, "data": CartSerializer(cart, context={"request": request}).data}
        )


class ClearCartView(APIView):
    """Remove all items from the cart."""

    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        return Response({"success": True, "message": "Cart cleared."})


class MergeCartView(APIView):
    """
    Merge an anonymous (session) cart into the authenticated user's cart.
    Call this immediately after login.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.data.get("session_key") or request.session.session_key
        if not session_key:
            return Response(
                {"success": False, "message": "No session key provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            anon_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
        except Cart.DoesNotExist:
            return Response({"success": True, "message": "No session cart to merge."})

        user_cart, _ = Cart.objects.get_or_create(user=request.user)

        for anon_item in anon_cart.items.all():
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=anon_item.product,
                variant=anon_item.variant,
                defaults={
                    "quantity": anon_item.quantity,
                    "unit_price": anon_item.unit_price,
                },
            )
            if not created:
                user_item.quantity += anon_item.quantity
                user_item.save(update_fields=["quantity", "updated_at"])

        anon_cart.delete()

        return Response(
            {
                "success": True,
                "message": "Cart merged successfully.",
                "data": CartSerializer(user_cart, context={"request": request}).data,
            }
        )
