from django.contrib import admin
from .models import ConfirmPaymentQueue, ConfirmTamdidPaymentQueue, Prices
# Register your models here.

admin.site.register(ConfirmPaymentQueue)
admin.site.register(ConfirmTamdidPaymentQueue)
admin.site.register(Prices)