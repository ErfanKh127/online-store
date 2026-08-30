from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from stores.models import Store


class StoreAPITestCase(APITestCase):

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
            description="Test description",
            owner=self.owner,
            is_active=True,
        )

        self.list_url = reverse("store-list")

        self.detail_url = reverse(
            "store-detail",
            kwargs={"pk": self.store.pk},
        )

    def test_anonymous_user_can_list_stores(self):
        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_anonymous_user_can_retrieve_store(self):
        response = self.client.get(
            self.detail_url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_anonymous_user_cannot_create_store(self):
        response = self.client.post(
            self.list_url,
            {
                "name": "New Store",
                "slug": "new-store",
                "description": "New description",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_create_store(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.post(
            self.list_url,
            {
                "name": "New Store",
                "slug": "new-store",
                "description": "New description",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        store = Store.objects.get(
            slug="new-store",
        )

        self.assertEqual(
            store.owner,
            self.other_user,
        )

    def test_user_cannot_set_another_owner_when_creating_store(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.post(
            self.list_url,
            {
                "name": "Fake Store",
                "slug": "fake-store",
                "description": "Fake description",
                "owner": self.owner.pk,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        store = Store.objects.get(
            slug="fake-store",
        )

        self.assertEqual(
            store.owner,
            self.other_user,
        )

    def test_store_owner_can_update_store(self):
        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.patch(
            self.detail_url,
            {
                "name": "Updated Store",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.store.refresh_from_db()

        self.assertEqual(
            self.store.name,
            "Updated Store",
        )

    def test_non_owner_cannot_update_store(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.patch(
            self.detail_url,
            {
                "name": "Hacked Store",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_store_owner_can_delete_store(self):
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
            Store.objects.filter(
                pk=self.store.pk,
            ).exists()
        )

    def test_non_owner_cannot_delete_store(self):
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