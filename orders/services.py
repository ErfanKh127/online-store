from django.db import transaction
from django.core.exceptions import ValidationError
from cart.models import Cart
from .models import Order, OrderItem

class CheckoutService:
    """
    Handles the checkout process: validates cart, creates order, updates stock.
    """

    @staticmethod
    @transaction.atomic
    def checkout(user, shipping_address):
        """
        Convert the user's cart into an Order.
        Returns the created Order object.
        """
        # 1. Get or create the user's cart
        cart, _ = Cart.objects.get_or_create(user=user)

        # 2. Validate cart is not empty
        if not cart.items.exists():
            raise ValidationError("Your cart is empty.")

        # 3. Validate stock for all items
        for cart_item in cart.items.all():
            product = cart_item.product
            if product.stock < cart_item.quantity:
                raise ValidationError(
                    f"Not enough stock for '{product.name}'. "
                    f"Available: {product.stock}, requested: {cart_item.quantity}"
                )

        # 4. Calculate total price
        total_price = cart.get_total_price()

        # 5. Create the order
        order = Order.objects.create(
            user=user,
            total_price=total_price,
            shipping_address=shipping_address,
            status=Order.OrderStatus.PENDING
        )

        # 6. Create order items (snapshot) and reduce product stock
        for cart_item in cart.items.all():
            product = cart_item.product

            # Reduce stock
            product.stock -= cart_item.quantity
            product.save(update_fields=['stock'])

            # Create order item snapshot
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_price=product.price,
                quantity=cart_item.quantity
            )

        # 7. Clear the cart (delete all cart items, or delete cart entirely)
        cart.items.all().delete()
        # Optionally keep the cart object for future use – we just clear its items.

        return order