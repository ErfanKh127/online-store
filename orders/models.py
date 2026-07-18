from django.db import models
from django.conf import settings
from common.models import BaseModel

class Order(BaseModel):
    """Main order model."""

    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELED = 'canceled', 'Canceled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    total_price = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0   # <-- add this
)
    shipping_address = models.TextField()
    # Optional: tracking number, payment method, etc.
    tracking_code = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # reference to payment gateway

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def can_be_paid(self):
        return self.status == self.OrderStatus.PENDING


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def get_total_price(self):
    # Safely multiply, default to 0 if either is None
        price = self.price or 0
        qty = self.quantity or 0
        return price * qty
        
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=255)   # snapshot of product name
    product_price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot of price at checkout
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

   