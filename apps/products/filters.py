"""
django-filter FilterSet for the Product model.
"""

import django_filters

from .models import Category, Product, Tag


class ProductFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.filter(is_active=True))
    category_slug = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="base_price", lookup_expr="lte")
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
        conjoined=False,
    )
    is_featured = django_filters.BooleanFilter()
    is_in_stock = django_filters.BooleanFilter(method="filter_in_stock")
    on_sale = django_filters.BooleanFilter(method="filter_on_sale")

    class Meta:
        model = Product
        fields = [
            "category",
            "category_slug",
            "min_price",
            "max_price",
            "tags",
            "is_featured",
            "is_in_stock",
            "on_sale",
        ]

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_on_sale(self, queryset, name, value):
        if value:
            return queryset.filter(sale_price__isnull=False)
        return queryset.filter(sale_price__isnull=True)
