from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from stores.models import Store
from products.models import Product
from orders.models import Order
from payments.models import Payment


class PaymentAPITestCase(APITestCase):

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
            price=Decimal("100.00"),
            stock=10,
            is_active=True,
        )

        self.order = Order.objects.create(
            user=self.owner,
            status=Order.OrderStatus.PENDING,
            total_price=Decimal("100.00"),
            shipping_address="Test Address",
        )

        self.initiate_url = reverse(
            "initiate-payment",
            kwargs={"order_id": self.order.id},
        )

        self.verify_url = reverse("verify-payment")

    def test_anonymous_user_cannot_initiate_payment(self):
        response = self.client.post(self.initiate_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @patch("payments.views.ZarinpalService.request_payment")
    def test_order_owner_can_initiate_payment(self, mock_request_payment):
        mock_request_payment.return_value = (
            True,
            "TEST_AUTHORITY",
            "Payment request created successfully.",
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(self.initiate_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "payment_id",
            response.data,
        )

        self.assertIn(
            "payment_url",
            response.data,
        )

        self.assertEqual(
            response.data["authority"],
            "TEST_AUTHORITY",
        )

        payment = Payment.objects.get(
            id=response.data["payment_id"],
        )

        self.assertEqual(
            payment.order,
            self.order,
        )

        self.assertEqual(
            payment.amount,
            Decimal("100.00"),
        )

        self.assertEqual(
            payment.status,
            Payment.PaymentStatus.PENDING,
        )

        self.assertEqual(
            payment.authority,
            "TEST_AUTHORITY",
        )

    def test_other_user_cannot_initiate_payment_for_order(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.post(self.initiate_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch("payments.views.ZarinpalService.request_payment")
    def test_already_paid_order_cannot_be_paid_again(
        self,
        mock_request_payment,
    ):
        self.order.status = Order.OrderStatus.PAID
        self.order.save(update_fields=["status"])

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(self.initiate_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"],
            "Order is already paid.",
        )

        mock_request_payment.assert_not_called()

    @patch("payments.views.ZarinpalService.request_payment")
    def test_pending_payment_is_reused(self, mock_request_payment):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            authority="EXISTING_AUTHORITY",
            status=Payment.PaymentStatus.PENDING,
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(self.initiate_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["payment_id"],
            payment.id,
        )

        self.assertIn(
            "payment_url",
            response.data,
        )

        mock_request_payment.assert_not_called()

    @patch("payments.views.ZarinpalService.request_payment")
    def test_failed_payment_request_marks_payment_as_failed(
        self,
        mock_request_payment,
    ):
        mock_request_payment.return_value = (
            False,
            None,
            "Zarinpal error",
        )

        self.client.force_authenticate(
            user=self.owner,
        )

        response = self.client.post(self.initiate_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        payment = Payment.objects.get(
            order=self.order,
        )

        self.assertEqual(
            payment.status,
            Payment.PaymentStatus.FAILED,
        )

    def test_verify_payment_requires_payment_id(self):
        response = self.client.get(
            self.verify_url,
            {
                "Authority": "TEST_AUTHORITY",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_verify_payment_requires_authority(self):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            status=Payment.PaymentStatus.PENDING,
        )

        response = self.client.get(
            self.verify_url,
            {
                "payment_id": payment.id,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_canceled_payment_is_marked_as_failed(self):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            authority="TEST_AUTHORITY",
            status=Payment.PaymentStatus.PENDING,
        )

        response = self.client.get(
            self.verify_url,
            {
                "payment_id": payment.id,
                "Authority": "TEST_AUTHORITY",
                "Status": "NOK",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.PaymentStatus.FAILED,
        )

        self.assertEqual(
            response.json()["status"],
            "failed",
        )

    @patch("payments.views.ZarinpalService.verify_payment")
    def test_successful_payment_updates_payment_and_order(
        self,
        mock_verify_payment,
    ):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            authority="TEST_AUTHORITY",
            status=Payment.PaymentStatus.PENDING,
        )

        mock_verify_payment.return_value = (
            True,
            "TEST_REF_ID",
            "Payment verified successfully.",
        )

        response = self.client.get(
            self.verify_url,
            {
                "payment_id": payment.id,
                "Authority": "TEST_AUTHORITY",
                "Status": "OK",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.PaymentStatus.PAID,
        )

        self.assertEqual(
            payment.ref_id,
            "TEST_REF_ID",
        )

        self.assertEqual(
            self.order.status,
            Order.OrderStatus.PAID,
        )

        self.assertEqual(
            self.order.payment_id,
            "TEST_REF_ID",
        )

        self.assertEqual(
            response.json()["status"],
            "paid",
        )

        self.assertEqual(
            response.json()["ref_id"],
            "TEST_REF_ID",
        )

    @patch("payments.views.ZarinpalService.verify_payment")
    def test_failed_payment_verification_marks_payment_as_failed(
        self,
        mock_verify_payment,
    ):
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_price,
            authority="TEST_AUTHORITY",
            status=Payment.PaymentStatus.PENDING,
        )

        mock_verify_payment.return_value = (
            False,
            None,
            "Verification failed",
        )

        response = self.client.get(
            self.verify_url,
            {
                "payment_id": payment.id,
                "Authority": "TEST_AUTHORITY",
                "Status": "OK",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        payment.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.PaymentStatus.FAILED,
        )