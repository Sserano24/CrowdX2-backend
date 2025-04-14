from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'campaign', 'amount', 'stripe_session_id', 'created_at')
    list_filter = ('campaign',)
    search_fields = ('stripe_session_id',)
