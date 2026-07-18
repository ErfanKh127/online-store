from django.db import models
from django.conf import settings
from common.models import BaseModel

class Cart(BaseModel):
    """
    A shopping cart belonging to a single user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total_price(self):
        """Calculate the total price of all items in the cart."""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        """Return the total number of items (sum of quantities)."""
        return sum(item.quantity for item in self.items.all())


class CartItem(BaseModel):
    """
    A single product line inside a cart.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')  # Prevent duplicate product entries

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """Return the total price for this line item."""
        return self.product.price * self.quantity