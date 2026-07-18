import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from orders.models import Order
from .models import Payment

class ZarinpalService:
    """
    Handles Zarinpal payment gateway operations.
    Using sandbox mode by default – set ZARINPAL_SANDBOX=True in .env.
    """

    SANDBOX_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
    SANDBOX_PAY_START = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'
    LIVE_URL = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    LIVE_PAY_START = 'https://www.zarinpal.com/pg/StartPay/{authority}'
    VERIFY_URL = 'https://api.zarinpal.com/pg/v4/payment/verify.json'

    @classmethod
    def _get_merchant_id(cls):
        merchant = settings.ZARINPAL_MERCHANT_ID
        if not merchant:
            raise ValueError("ZARINPAL_MERCHANT_ID is not set in environment variables.")
        return merchant

    @classmethod
    def _is_sandbox(cls):
        return getattr(settings, 'ZARINPAL_SANDBOX', True)

    @classmethod
    def _get_request_url(cls):
        return cls.SANDBOX_URL if cls._is_sandbox() else cls.LIVE_URL

    @classmethod
    def _get_pay_start_url(cls, authority):
        url_template = cls.SANDBOX_PAY_START if cls._is_sandbox() else cls.LIVE_PAY_START
        return url_template.format(authority=authority)

    @classmethod
    def request_payment(cls, payment: Payment, callback_url: str):
        """
        Sends a request to Zarinpal to create a new payment.
        Returns (success, authority, message).
        """
        merchant_id = cls._get_merchant_id()
        request_url = cls._get_request_url()

        payload = {
            'merchant_id': merchant_id,
            'amount': int(payment.amount),   # Zarinpal expects amount as integer (no decimals)
            'callback_url': callback_url,
            'description': f'Payment for Order #{payment.order.id} - {payment.order.user.username}',
            'metadata': {
                'order_id': str(payment.order.id),
                'user_id': str(payment.order.user.id),
            }
        }

        try:
            response = requests.post(request_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            print("========== ZARINPAL RESPONSE ==========")
            print(data)
            print("=======================================")

            # Save raw response for debugging
            payment.raw_response = data
            payment.save(update_fields=['raw_response'])

            if data.get('data', {}).get('code') == 100:
                authority = data['data']['authority']
                payment.authority = authority
                payment.save(update_fields=['authority'])
                return True, authority, 'Payment request created successfully.'
            else:
                error_code = data.get('errors', {}).get('code')
                error_message = data.get('errors', {}).get('message', 'Unknown error')
                return False, None, f'Zarinpal error: {error_code} - {error_message}'

        except requests.exceptions.RequestException as e:
            return False, None, f'Network error: {str(e)}'

    @classmethod
    def verify_payment(cls, payment: Payment, authority: str):
        """
        Verifies a payment after the user returns from the gateway.
        Returns (is_paid, ref_id, message).
        """
        merchant_id = cls._get_merchant_id()
        amount = int(payment.amount)

        payload = {
            'merchant_id': merchant_id,
            'amount': amount,
            'authority': authority,
        }

        try:
            response = requests.post(cls.VERIFY_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            payment.raw_response = data
            payment.save(update_fields=['raw_response'])

            if data.get('data', {}).get('code') == 100:
                ref_id = data['data']['ref_id']
                return True, ref_id, 'Payment verified successfully.'
            else:
                error_code = data.get('errors', {}).get('code', 'unknown')
                error_message = data.get('errors', {}).get('message', 'Verification failed')
                return False, None, f'Verification failed: {error_code} - {error_message}'

        except requests.exceptions.RequestException as e:
            return False, None, f'Network error: {str(e)}'