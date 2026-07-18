from django.db import models
from django.conf import settings
from common.models import BaseModel

class Payment(BaseModel):
    """
    Tracks payment transactions for orders.
    """

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        CANCELED = 'canceled', 'Canceled'

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    authority = models.CharField(max_length=100, blank=True, null=True)   # Zarinpal authority token
    ref_id = models.CharField(max_length=100, blank=True, null=True)      # Zarinpal reference ID
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    # Optional: store the raw response from Zarinpal for debugging
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment #{self.id} - Order #{self.order.id}"

    def mark_as_paid(self, ref_id):
        self.status = self.PaymentStatus.PAID
        self.ref_id = ref_id
        self.save(update_fields=['status', 'ref_id'])

    def mark_as_failed(self):
        self.status = self.PaymentStatus.FAILED
        self.save(update_fields=['status'])