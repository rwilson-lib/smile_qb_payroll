from django.contrib import admin
from .models import Account, Transaction, GeneralLedger, LineItem

# Register your models here.

admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(GeneralLedger)
admin.site.register(LineItem)
