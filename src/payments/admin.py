from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'campaign', 'amount', 'payment_method', 'status', 'paypal_order_id', 'created_at')
    list_filter = ('campaign', 'payment_method', 'status')
    search_fields = ('paypal_order_id',)
