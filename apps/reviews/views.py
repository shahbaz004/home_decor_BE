"""
Review views.
"""

from django.db.models import Avg, Count

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsOwner

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer


class ReviewViewSet(ModelViewSet):
    """
    List reviews by product, create reviews (authenticated), admin approve/delete.
    """

    serializer_class = ReviewSerializer
    pagination_class = StandardPagination
    parser_classes = [MultiPartParser, JSONParser]
    filterset_fields = ["product", "rating", "is_approved"]
    ordering_fields = ["rating", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action in ("approve", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            agg = queryset.aggregate(avg_rating=Avg("rating"))
            breakdown = {
                star: queryset.filter(rating=star).count()
                for star in range(1, 6)
            }
            response.data["average_rating"] = round(agg["avg_rating"] or 0, 1)
            response.data["rating_breakdown"] = breakdown
            return response
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        qs = Review.objects.select_related("user", "product").prefetch_related("images")
        if not self.request.user.is_staff:
            qs = qs.filter(is_approved=True)

        product_id = self.request.query_params.get("product_id")
        product_slug = self.request.query_params.get("product_slug")

        if product_id:
            qs = qs.filter(product__id=product_id)
        elif product_slug:
            qs = qs.filter(product__slug=product_slug)

        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        return ReviewSerializer

    def create(self, request, *args, **kwargs):
        serializer = ReviewCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Review submitted and pending approval.",
                "data": ReviewSerializer(review, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        """Approve a review to make it visible."""
        review = self.get_object()
        review.is_approved = True
        review.save(update_fields=["is_approved"])
        return Response({"success": True, "message": "Review approved."})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        """Reject a review."""
        review = self.get_object()
        review.is_approved = False
        review.save(update_fields=["is_approved"])
        return Response({"success": True, "message": "Review rejected."})
