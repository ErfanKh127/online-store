from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'status', 'authority', 'ref_id', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'authority', 'ref_id')
    readonly_fields = ('raw_response',)