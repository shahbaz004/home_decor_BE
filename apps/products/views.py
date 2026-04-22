"""
Product and category viewsets.
"""

from django.db.models import Prefetch
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.core.pagination import LargePagination, StandardPagination
from apps.core.permissions import IsAdminOrReadOnly

from .filters import ProductFilter
from .models import Category, Product, ProductImage, ProductVariant, Tag
from .serializers import (
    CategorySerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductListSerializer,
    ProductVariantSerializer,
    TagSerializer,
)


class CategoryViewSet(ModelViewSet):
    """CRUD for product categories. Public read, admin write."""

    queryset = Category.objects.select_related("parent").prefetch_related("children")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        parent = self.request.query_params.get("parent")
        if parent is None:
            qs = qs.filter(parent__isnull=True)  # Root categories only by default
        elif parent:
            qs = qs.filter(parent__slug=parent)
        return qs


class TagViewSet(ReadOnlyModelViewSet):
    """Read-only tag listing."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"


class ProductViewSet(ModelViewSet):
    """
    Full product CRUD.
    - List/detail: public
    - Create/update/delete: admin only
    """

    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "sku", "tags__name", "category__name"]
    ordering_fields = ["base_price", "created_at", "name", "stock"]
    ordering = ["-created_at"]
    lookup_field = "slug"
    parser_classes = [MultiPartParser, JSONParser]

    def get_queryset(self):
        qs = (
            Product.objects.select_related("category")
            .prefetch_related(
                "tags",
                Prefetch("images", queryset=ProductImage.objects.order_by("display_order", "-is_primary")),
                "variants",
            )
        )
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True, deleted_at__isnull=True)
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductCreateUpdateSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def get_pagination_class(self):
        if self.action == "list":
            return StandardPagination
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Record a product view asynchronously
        try:
            from apps.analytics.tasks import record_product_view
            session_key = request.session.session_key or ""
            user_id = str(request.user.id) if request.user.is_authenticated else None
            ip = request.META.get("REMOTE_ADDR", "")
            record_product_view.delay(str(instance.id), user_id, session_key, ip)
        except Exception:
            pass
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrReadOnly])
    def upload_images(self, request, slug=None):
        """Upload one or more images for a product."""
        product = self.get_object()
        images = request.FILES.getlist("images")
        if not images:
            return Response(
                {"success": False, "message": "No images provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        created = []
        for idx, img in enumerate(images):
            is_primary = idx == 0 and not product.images.filter(is_primary=True).exists()
            pi = ProductImage.objects.create(
                product=product,
                image=img,
                alt_text=request.data.get("alt_text", product.name),
                is_primary=is_primary,
                display_order=product.images.count(),
            )
            created.append(ProductImageSerializer(pi, context={"request": request}).data)

        return Response(
            {"success": True, "data": created},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def variants(self, request, slug=None):
        """Return all variants for a product."""
        product = self.get_object()
        variants = product.variants.filter(is_active=True)
        serializer = ProductVariantSerializer(variants, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def featured(self, request):
        """Return featured products."""
        qs = self.get_queryset().filter(is_featured=True)[:12]
        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def new_arrivals(self, request):
        """Return the 12 most recently added products."""
        qs = self.get_queryset().order_by("-created_at")[:12]
        serializer = ProductListSerializer(qs, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data})
