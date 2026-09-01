import requests
from django.conf import settings

from .models import Payment


class ZarinpalService:
    """
    Handles Zarinpal payment gateway operations.
    Uses sandbox mode by default.
    """

    SANDBOX_URL = (
        "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    )
    SANDBOX_VERIFY_URL = (
        "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    )
    SANDBOX_PAY_START = (
        "https://sandbox.zarinpal.com/pg/StartPay/{authority}"
    )

    LIVE_URL = (
        "https://api.zarinpal.com/pg/v4/payment/request.json"
    )
    LIVE_VERIFY_URL = (
        "https://api.zarinpal.com/pg/v4/payment/verify.json"
    )
    LIVE_PAY_START = (
        "https://www.zarinpal.com/pg/StartPay/{authority}"
    )

    @classmethod
    def _get_merchant_id(cls):
        merchant = getattr(
            settings,
            "ZARINPAL_MERCHANT_ID",
            None,
        )

        if not merchant:
            raise ValueError(
                "ZARINPAL_MERCHANT_ID is not set "
                "in environment variables."
            )

        return merchant

    @classmethod
    def _is_sandbox(cls):
        return getattr(
            settings,
            "ZARINPAL_SANDBOX",
            True,
        )

    @classmethod
    def _get_request_url(cls):
        if cls._is_sandbox():
            return cls.SANDBOX_URL

        return cls.LIVE_URL

    @classmethod
    def _get_verify_url(cls):
        if cls._is_sandbox():
            return cls.SANDBOX_VERIFY_URL

        return cls.LIVE_VERIFY_URL

    @classmethod
    def _get_pay_start_url(cls, authority):
        if cls._is_sandbox():
            return cls.SANDBOX_PAY_START.format(
                authority=authority
            )

        return cls.LIVE_PAY_START.format(
            authority=authority
        )

    @classmethod
    def request_payment(cls, payment: Payment, callback_url: str):
        """
        Sends a request to Zarinpal to create a new payment.

        Returns:
            (success, authority, message)
        """
        merchant_id = cls._get_merchant_id()
        request_url = cls._get_request_url()

        payload = {
            "merchant_id": merchant_id,
            "amount": int(payment.amount),
            "callback_url": callback_url,
            "description": (
                f"Payment for Order #{payment.order.id} - "
                f"{payment.order.user.username}"
            ),
            "metadata": {
                "order_id": str(payment.order.id),
                "user_id": str(payment.order.user.id),
            },
        }

        try:
            response = requests.post(
                request_url,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()

            payment.raw_response = data
            payment.save(
                update_fields=["raw_response"]
            )

            response_data = data.get("data", {})

            if response_data.get("code") == 100:
                authority = response_data.get("authority")

                if not authority:
                    return (
                        False,
                        None,
                        "Zarinpal response did not contain an authority.",
                    )

                payment.authority = authority
                payment.save(
                    update_fields=["authority"]
                )

                return (
                    True,
                    authority,
                    "Payment request created successfully.",
                )

            errors = data.get("errors", {})

            error_code = errors.get("code", "unknown")
            error_message = errors.get(
                "message",
                "Unknown error",
            )

            return (
                False,
                None,
                f"Zarinpal error: {error_code} - {error_message}",
            )

        except requests.exceptions.RequestException as exc:
            return (
                False,
                None,
                f"Network error: {str(exc)}",
            )

    @classmethod
    def verify_payment(
        cls,
        payment: Payment,
        authority: str,
    ):
        """
        Verifies a payment after the user returns
        from the gateway.

        Returns:
            (is_paid, ref_id, message)
        """
        merchant_id = cls._get_merchant_id()
        verify_url = cls._get_verify_url()

        payload = {
            "merchant_id": merchant_id,
            "amount": int(payment.amount),
            "authority": authority,
        }

        try:
            response = requests.post(
                verify_url,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()

            payment.raw_response = data
            payment.save(
                update_fields=["raw_response"]
            )

            response_data = data.get("data", {})

            if response_data.get("code") == 100:
                ref_id = response_data.get("ref_id")

                if not ref_id:
                    return (
                        False,
                        None,
                        "Zarinpal response did not contain a ref_id.",
                    )

                return (
                    True,
                    ref_id,
                    "Payment verified successfully.",
                )

            errors = data.get("errors", {})

            error_code = errors.get(
                "code",
                "unknown",
            )
            error_message = errors.get(
                "message",
                "Verification failed",
            )

            return (
                False,
                None,
                f"Verification failed: "
                f"{error_code} - {error_message}",
            )

        except requests.exceptions.RequestException as exc:
            return (
                False,
                None,
                f"Network error: {str(exc)}",
            )