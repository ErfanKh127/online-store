from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Order
from .serializers import OrderSerializer
from .services import CheckoutService



class OrderViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        shipping_address = serializer.validated_data.get(
            "shipping_address"
        )

        if not shipping_address:
            raise ValidationError(
                {
                    "shipping_address": (
                        "Shipping address is required."
                    )
                }
            )

        try:
            order = CheckoutService.checkout(
                user=self.request.user,
                shipping_address=shipping_address,
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                {"detail": exc.messages}
            )

        serializer.instance = order