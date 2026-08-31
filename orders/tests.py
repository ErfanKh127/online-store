from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from cart.models import Cart, CartItem
from products.models import Product
from stores.models import Store
from .models import Order, OrderItem


class OrderAPITestCase(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
        )

        self.customer = User.objects.create_user(
            username="customer",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            password="testpass123",
        )

        self.store = Store.objects.create(
            name="Test Store",
            slug="test-store",
            owner=self.owner,
        )

        self.product = Product.objects.create(
            store=self.store,
            name="Test Product",
            slug="test-product",
            description="Test description",
            price="100.00",
            stock=10,
            is_active=True,
        )

        self.product_2 = Product.objects.create(
            store=self.store,
            name="Second Product",
            slug="second-product",
            description="Second description",
            price="50.00",
            stock=20,
            is_active=True,
        )

        self.list_url = reverse("order-list")

    def create_cart(self, user, quantity=1):
        cart = Cart.objects.create(user=user)

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=quantity,
        )

        return cart

    def test_anonymous_user_cannot_list_orders(self):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_list_orders(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_user_can_only_see_own_orders(self):
        own_order = Order.objects.create(
            user=self.customer,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("100.00"),
            shipping_address="Customer Address",
        )

        Order.objects.create(
            user=self.other_user,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("200.00"),
            shipping_address="Other Address",
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        results = response.data

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0]["id"],
            own_order.id,
        )

    def test_authenticated_user_can_checkout(self):
        self.create_cart(
            user=self.customer,
            quantity=2,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.customer,
        )

        self.assertEqual(
            order.total_price,
            Decimal("200.00"),
        )

        self.assertEqual(
            order.status,
            Order.OrderStatus.PENDING,
        )

        self.assertEqual(
            order.shipping_address,
            "123 Test Street",
        )

    def test_checkout_creates_order_item_snapshot(self):
        self.create_cart(
            user=self.customer,
            quantity=2,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.customer,
        )

        item = OrderItem.objects.get(
            order=order,
        )

        self.assertEqual(
            item.product,
            self.product,
        )

        self.assertEqual(
            item.product_name,
            self.product.name,
        )

        self.assertEqual(
            item.product_price,
            Decimal("100.00"),
        )

        self.assertEqual(
            item.quantity,
            2,
        )

    def test_checkout_reduces_product_stock(self):
        self.create_cart(
            user=self.customer,
            quantity=3,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            7,
        )

    def test_checkout_clears_cart(self):
        cart = self.create_cart(
            user=self.customer,
            quantity=2,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertFalse(
            cart.items.exists(),
        )

    def test_checkout_empty_cart_returns_400(self):
        Cart.objects.create(
            user=self.customer,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_checkout_without_cart_returns_400(self):
        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_checkout_with_insufficient_stock_returns_400(self):
        self.create_cart(
            user=self.customer,
            quantity=11,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            10,
        )

    def test_user_can_retrieve_own_order(self):
        order = Order.objects.create(
            user=self.customer,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("100.00"),
            shipping_address="Customer Address",
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        detail_url = reverse(
            "order-detail",
            kwargs={"pk": order.pk},
        )

        response = self.client.get(detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            order.id,
        )

    def test_user_cannot_retrieve_other_users_order(self):
        order = Order.objects.create(
            user=self.other_user,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("100.00"),
            shipping_address="Other Address",
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        detail_url = reverse(
            "order-detail",
            kwargs={"pk": order.pk},
        )

        response = self.client.get(detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_checkout_does_not_allow_client_to_set_user(self):
        self.create_cart(
            user=self.customer,
            quantity=1,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "user": self.other_user.pk,
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.customer,
        )

        self.assertNotEqual(
            order.user,
            self.other_user,
        )

    def test_checkout_does_not_allow_client_to_set_total_price(self):
        self.create_cart(
            user=self.customer,
            quantity=1,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
                "total_price": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.customer,
        )

        self.assertEqual(
            order.total_price,
            Decimal("100.00"),
        )

    def test_checkout_does_not_allow_client_to_set_status(self):
        self.create_cart(
            user=self.customer,
            quantity=1,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
                "status": Order.OrderStatus.PAID,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.customer,
        )

        self.assertEqual(
            order.status,
            Order.OrderStatus.PENDING,
        )

    def test_checkout_requires_shipping_address(self):
        self.create_cart(
            user=self.customer,
            quantity=1,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_checkout_multiple_products_calculates_total_correctly(self):
        cart = Cart.objects.create(
            user=self.customer,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product_2,
            quantity=3,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        order = Order.objects.get(
            user=self.customer,
        )

        self.assertEqual(
            order.total_price,
            Decimal("350.00"),
        )

        self.assertEqual(
            order.items.count(),
            2,
        )

    def test_checkout_reduces_stock_for_multiple_products(self):
        cart = Cart.objects.create(
            user=self.customer,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
        )

        CartItem.objects.create(
            cart=cart,
            product=self.product_2,
            quantity=3,
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        response = self.client.post(
            self.list_url,
            {
                "shipping_address": "123 Test Street",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.product.refresh_from_db()
        self.product_2.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            8,
        )

        self.assertEqual(
            self.product_2.stock,
            17,
        )

    def test_user_cannot_update_order(self):
        order = Order.objects.create(
            user=self.customer,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("100.00"),
            shipping_address="Customer Address",
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        detail_url = reverse(
            "order-detail",
            kwargs={"pk": order.pk},
        )

        response = self.client.patch(
            detail_url,
            {
                "shipping_address": "Changed Address",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_user_cannot_delete_order(self):
        order = Order.objects.create(
            user=self.customer,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("100.00"),
            shipping_address="Customer Address",
        )

        self.client.force_authenticate(
            user=self.customer,
        )

        detail_url = reverse(
            "order-detail",
            kwargs={"pk": order.pk},
        )

        response = self.client.delete(detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )