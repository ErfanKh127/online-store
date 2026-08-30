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

        self.other_store = Store.objects.create(
            name="Other Store",
            slug="other-store",
            owner=self.other_user,
        )

        self.product = Product.objects.create(
            store=self.store,
            name="Test Product",
            slug="test-product",
            description="Test description",
            price="100.00",
            stock=10,
            is_active=True,
            category="Electronics",
        )

        self.product_2 = Product.objects.create(
            store=self.store,
            name="Another Product",
            slug="another-product",
            description="Another description",
            price="200.00",
            stock=20,
            is_active=True,
            category="Books",
        )

        self.product_3 = Product.objects.create(
            store=self.store,
            name="Expensive Product",
            slug="expensive-product",
            description="Expensive description",
            price="500.00",
            stock=5,
            is_active=True,
            category="Electronics",
        )

        self.other_store_product = Product.objects.create(
            store=self.other_store,
            name="Other Store Product",
            slug="other-store-product",
            description="Product from another store",
            price="300.00",
            stock=15,
            is_active=True,
            category="Electronics",
        )

        self.list_url = reverse("product-list")

        self.detail_url = reverse(
            "product-detail",
            kwargs={"pk": self.product.pk},
        )

    # ---------------------------------------------------------
    # Basic access
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def test_search_products_by_name(self):
        response = self.client.get(
            self.list_url,
            {
                "search": "Expensive",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["name"],
            "Expensive Product",
        )

    def test_search_products_by_description(self):
        response = self.client.get(
            self.list_url,
            {
                "search": "another description",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["name"],
            "Another Product",
        )

    # ---------------------------------------------------------
    # Filtering
    # ---------------------------------------------------------

    def test_filter_products_by_store(self):
        response = self.client.get(
            self.list_url,
            {
                "store": self.store.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )

    def test_filter_products_by_category(self):
        response = self.client.get(
            self.list_url,
            {
                "category": "Electronics",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )

    def test_filter_products_by_min_price(self):
        response = self.client.get(
            self.list_url,
            {
                "min_price": "200",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            3,
        )

    def test_filter_products_by_max_price(self):
        response = self.client.get(
            self.list_url,
            {
                "max_price": "200",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_filter_products_by_price_range(self):
        response = self.client.get(
            self.list_url,
            {
                "min_price": "150",
                "max_price": "350",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

    # ---------------------------------------------------------
    # Ordering
    # ---------------------------------------------------------

    def test_order_products_by_price_ascending(self):
        response = self.client.get(
            self.list_url,
            {
                "ordering": "price",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        prices = [
            Decimal(str(product["price"]))
            for product in response.data["results"]
        ]

        self.assertEqual(
            prices,
            sorted(prices),
        )

    def test_order_products_by_price_descending(self):
        response = self.client.get(
            self.list_url,
            {
                "ordering": "-price",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        prices = [
            Decimal(str(product["price"]))
            for product in response.data["results"]
        ]

        self.assertEqual(
            prices,
            sorted(prices, reverse=True),
        )

    def test_order_products_by_name(self):
        response = self.client.get(
            self.list_url,
            {
                "ordering": "name",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        names = [
            product["name"]
            for product in response.data["results"]
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    def test_products_are_paginated(self):
        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "count",
            response.data,
        )

        self.assertIn(
            "next",
            response.data,
        )

        self.assertIn(
            "previous",
            response.data,
        )

        self.assertIn(
            "results",
            response.data,
        )

    def test_page_size_query_parameter(self):
        response = self.client.get(
            self.list_url,
            {
                "page_size": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )