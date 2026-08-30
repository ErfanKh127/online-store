from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from stores.models import Store
from products.models import Product


class ProductAPITestCase(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
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

        self.list_url = reverse("product-list")

        self.detail_url = reverse(
            "product-detail",
            kwargs={"pk": self.product.pk},
        )

    def test_anonymous_user_can_list_products(self):
        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_anonymous_user_can_retrieve_product(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(
            self.list_url,
            {
                "store": self.store.pk,
                "name": "New Product",
                "slug": "new-product",
                "price": "200.00",
                "stock": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_store_owner_can_create_product(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(
            self.list_url,
            {
                "store": self.store.pk,
                "name": "New Product",
                "slug": "new-product",
                "price": "200.00",
                "stock": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_non_owner_cannot_create_product_in_other_store(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.post(
            self.list_url,
            {
                "store": self.store.pk,
                "name": "Fake Product",
                "slug": "fake-product",
                "price": "500.00",
                "stock": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_store_owner_can_update_product(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.patch(
            self.detail_url,
            {
                "price": "150.00",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.price,
            Decimal("150.00"),
        )

    def test_non_owner_cannot_update_product(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.patch(
            self.detail_url,
            {
                "price": "999.00",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_store_owner_can_delete_product(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.delete(
            self.detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Product.objects.filter(
                pk=self.product.pk,
            ).exists()
        )

    def test_non_owner_cannot_delete_product(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.delete(
            self.detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )