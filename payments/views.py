from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from orders.models import Order
from .models import Payment
from .services import ZarinpalService

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request, order_id):
    """
    Create a Payment record and redirect to Zarinpal.
    Expects: order_id in URL.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 1. Check if order is already paid
    if order.status == Order.OrderStatus.PAID:
        return Response({'error': 'Order is already paid.'}, status=400)

    # 2. Check if a pending payment already exists
    existing_payment = Payment.objects.filter(order=order, status=Payment.PaymentStatus.PENDING).first()
    if existing_payment:
        # Re-use existing pending payment – redirect user to Zarinpal again
        pay_url = ZarinpalService._get_pay_start_url(existing_payment.authority)
        return Response({'payment_url': pay_url, 'payment_id': existing_payment.id})

    # 3. Create a new payment record
    payment = Payment.objects.create(
        order=order,
        amount=order.total_price,
        status=Payment.PaymentStatus.PENDING
    )

    # 4. Build callback URL (use your domain – adjust accordingly)
    callback_url = f"{settings.BASE_URL}/api/payments/verify/?payment_id={payment.id}"

    # 5. Request payment from Zarinpal
    success, authority, message = ZarinpalService.request_payment(payment, callback_url)

    if not success:
        payment.status = Payment.PaymentStatus.FAILED
        payment.save(update_fields=['status'])
        return Response({'error': message}, status=400)

    # 6. Return the payment URL to the client
    pay_url = ZarinpalService._get_pay_start_url(authority)
    return Response({
        'payment_id': payment.id,
        'payment_url': pay_url,
        'authority': authority,
        'message': message
    })


@api_view(['GET'])
def verify_payment(request):
    """
    Zarinpal redirects the user to this URL after payment attempt.
    We verify the payment and update order status.
    """
    payment_id = request.GET.get('payment_id')
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')  # 'OK' or 'NOK'

    if not payment_id or not authority:
        return JsonResponse({'error': 'Missing payment_id or Authority parameter.'}, status=400)

    payment = get_object_or_404(Payment, id=payment_id)

    # If user canceled payment
    if status == 'NOK':
        payment.mark_as_failed()
        return JsonResponse({'message': 'Payment was canceled by user.', 'status': 'failed'})

    # Verify with Zarinpal
    is_paid, ref_id, message = ZarinpalService.verify_payment(payment, authority)

    if is_paid:
        # Update payment
        payment.mark_as_paid(ref_id)

        # Update order
        order = payment.order
        order.status = Order.OrderStatus.PAID
        order.payment_id = ref_id
        order.save(update_fields=['status', 'payment_id'])

        return JsonResponse({
            'message': 'Payment successful!',
            'ref_id': ref_id,
            'order_id': order.id,
            'status': 'paid'
        })
    else:
        payment.mark_as_failed()
        return JsonResponse({
            'message': f'Payment verification failed: {message}',
            'status': 'failed'
        }, status=400)