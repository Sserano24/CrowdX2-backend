from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'campaign',
        'amount',      # gross amount
        'fee',
        'net_amount',
        'payment_method',
        'status',
        'paypal_order_id',
        'created_at',
    )
    list_filter = ('campaign', 'payment_method', 'status')
    search_fields = ('paypal_order_id',)

    # Optional: rename headers in admin table
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def amount_label(self, obj):
        return f"${obj.amount:.2f}"
    amount_label.short_description = "Gross Amount"

    def fee_label(self, obj):
        return f"${obj.fee:.2f}" if obj.fee else "-"
    fee_label.short_description = "PayPal Fee"

    def net_label(self, obj):
        return f"${obj.net_amount:.2f}" if obj.net_amount else "-"
    net_label.short_description = "Net Amount"

