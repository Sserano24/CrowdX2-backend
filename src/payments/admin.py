from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'campaign', 'amount', 'payment_id', 'created_at')
    list_filter = ('campaign',)
    search_fields = ('payment_id',)
