from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from common.pagination import ProductPagination

from .filters import ProductFilter
from .models import Product
from .permissions import IsStoreOwner
from .serializers import ProductSerializer


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    pagination_class = ProductPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_class = ProductFilter

    search_fields = [
        "name",
        "description",
    ]

    ordering_fields = [
        "price",
        "created_at",
        "name",
    ]

    ordering = [
        "-created_at",
    ]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]

        if self.action == "create":
            return [IsAuthenticated()]

        return [
            IsAuthenticated(),
            IsStoreOwner(),
        ]

    def perform_create(self, serializer):
        store = serializer.validated_data["store"]

        if store.owner != self.request.user:
            raise PermissionDenied(
                "You can only create products for your own store."
            )

        serializer.save()

    def perform_update(self, serializer):
        product = self.get_object()

        store = serializer.validated_data.get(
            "store",
            product.store
        )

        if store.owner != self.request.user:
            raise PermissionDenied(
                "You can only use your own store."
            )

        serializer.save()