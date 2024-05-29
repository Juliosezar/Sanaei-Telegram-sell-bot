from django.shortcuts import render
from .models import Prices as PriceModel
from .models import Payment
from custumers.models import Customer

class Wallet:
    @classmethod
    def get_wallet_anount(cls, user_id):
        amount = Customer.objects.get(userid=user_id).wallet
        return amount

    @classmethod
    def add_to_wallet(cls, user_id, amount):
        wallet_obj = Customer.objects.get(userid=user_id)
        wallet_obj.wallet = wallet_obj.wallet + amount
        wallet_obj.save()

class Prices:
    @classmethod
    def get_expire_times(cls):
        price_obj = PriceModel.objects.all()
        months = [m.expire_limit for m in price_obj]
        months = list(set(months)) # for delete same values
        return months

    @classmethod
    def get_usage_and_prices_of_selected_month(cls, month):
        price_obj = PriceModel.objects.filter(expire_limit=month)
        return price_obj

