"""
Wishlist views – list, add, remove, and move to cart.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart, CartItem

from .models import WishlistItem
from .serializers import MoveToCartSerializer, WishlistItemSerializer


class WishlistView(APIView):
    """List all wishlist items for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related("product", "variant")
        serializer = WishlistItemSerializer(items, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data})

    def post(self, request):
        """Add a product to the wishlist."""
        serializer = WishlistItemSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Added to wishlist.",
                "data": WishlistItemSerializer(item, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class WishlistItemView(APIView):
    """Remove a specific wishlist item."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = WishlistItem.objects.get(id=item_id, user=request.user)
        except WishlistItem.DoesNotExist:
            return Response(
                {"success": False, "message": "Wishlist item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        return Response({"success": True, "message": "Removed from wishlist."})


class MoveToCartView(APIView):
    """Move a wishlist item into the user's cart."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MoveToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wishlist_item_id = serializer.validated_data["wishlist_item_id"]
        quantity = serializer.validated_data["quantity"]

        try:
            wi = WishlistItem.objects.get(id=wishlist_item_id, user=request.user)
        except WishlistItem.DoesNotExist:
            return Response(
                {"success": False, "message": "Wishlist item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        product = wi.product
        variant = wi.variant
        available = variant.stock if variant else product.stock
        if available < quantity:
            return Response(
                {"success": False, "message": f"Only {available} units available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        unit_price = variant.effective_price if variant else product.effective_price

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={"quantity": quantity, "unit_price": unit_price},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save(update_fields=["quantity", "updated_at"])

        wi.delete()

        return Response(
            {"success": True, "message": "Item moved to cart."},
            status=status.HTTP_200_OK,
        )
