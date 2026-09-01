from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order

from .models import Payment
from .services import ZarinpalService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request, order_id):
    """
    Create a Payment record and request a payment from Zarinpal.

    Only the owner of the order can initiate its payment.
    """

    # 1. Get the order belonging to the authenticated user
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    # 2. Do not allow payment for an already-paid order
    if order.status == Order.OrderStatus.PAID:
        return Response(
            {"error": "Order is already paid."},
            status=400,
        )

    # 3. Reuse an existing pending payment if one exists
    existing_payment = (
        Payment.objects
        .filter(
            order=order,
            status=Payment.PaymentStatus.PENDING,
        )
        .first()
    )

    if existing_payment:
        # If the payment already has an authority,
        # send the customer back to the gateway.
        if existing_payment.authority:
            pay_url = ZarinpalService._get_pay_start_url(
                existing_payment.authority
            )

            return Response(
                {
                    "payment_id": existing_payment.id,
                    "payment_url": pay_url,
                    "authority": existing_payment.authority,
                },
                status=200,
            )

    # 4. Create a new payment
    payment = Payment.objects.create(
        order=order,
        amount=order.total_price,
        status=Payment.PaymentStatus.PENDING,
    )

    # 5. Build callback URL from the current request.
    #
    # This avoids depending on settings.BASE_URL and works
    # correctly in tests and in development.
    callback_url = request.build_absolute_uri(
        f"/api/payments/verify/?payment_id={payment.id}"
    )

    # 6. Ask Zarinpal to create the payment
    success, authority, message = ZarinpalService.request_payment(
        payment=payment,
        callback_url=callback_url,
    )

    # 7. Payment request failed
    if not success:
        payment.status = Payment.PaymentStatus.FAILED
        payment.save(update_fields=["status"])

        return Response(
            {"error": message},
            status=400,
        )

    # 8. Save the authority returned by Zarinpal.
    #
    # The service normally saves this itself, but doing it here
    # makes the view robust when the service is mocked in tests.
    payment.authority = authority
    payment.save(update_fields=["authority"])

    # 9. Build the gateway URL
    pay_url = ZarinpalService._get_pay_start_url(authority)

    return Response(
        {
            "payment_id": payment.id,
            "payment_url": pay_url,
            "authority": authority,
            "message": message,
        },
        status=200,
    )


@api_view(["GET"])
def verify_payment(request):
    """
    Zarinpal redirects the customer here after payment.

    The payment is verified with Zarinpal and, if successful,
    both the Payment and Order are marked as paid.
    """

    payment_id = request.GET.get("payment_id")
    authority = request.GET.get("Authority")
    gateway_status = request.GET.get("Status")

    # 1. Validate required parameters
    if not payment_id or not authority:
        return JsonResponse(
            {
                "error": (
                    "Missing payment_id or Authority parameter."
                )
            },
            status=400,
        )

    # 2. Get the payment
    payment = get_object_or_404(
        Payment,
        id=payment_id,
    )

    # 3. If the customer canceled the payment
    if gateway_status == "NOK":
        payment.mark_as_failed()

        return JsonResponse(
            {
                "message": "Payment was canceled by user.",
                "status": "failed",
            },
            status=200,
        )

    # 4. Verify payment with Zarinpal
    is_paid, ref_id, message = ZarinpalService.verify_payment(
        payment=payment,
        authority=authority,
    )

    # 5. Successful payment
    if is_paid:
        payment.mark_as_paid(ref_id)

        order = payment.order
        order.status = Order.OrderStatus.PAID
        order.payment_id = ref_id
        order.save(
            update_fields=[
                "status",
                "payment_id",
            ]
        )

        return JsonResponse(
            {
                "message": "Payment successful!",
                "ref_id": ref_id,
                "order_id": order.id,
                "status": "paid",
            },
            status=200,
        )

    # 6. Verification failed
    payment.mark_as_failed()

    return JsonResponse(
        {
            "message": f"Payment verification failed: {message}",
            "status": "failed",
        },
        status=400,
    )