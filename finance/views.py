from django.shortcuts import render
from .models import Prices as PriceModel
# from .models import Payment
from custumers.models import Customer
from finance.models import ConfirmPaymentQueue as PaymentQueueModel
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



class Paying:
    @classmethod
    def pay_config_before_img(cls, user_id, price, uuid):
        user_obj = Customer.objects.get(userid=user_id)
        if PaymentQueueModel.objects.filter(userid=user_obj, status=0).exists():
            PaymentQueueModel.objects.get(userid=user_obj, status=0).delete()
        PaymentQueueModel.objects.create(
            userid=user_obj,
            price=price,
            status=0,
            config_in_queue=True,
            config_uuid=uuid,
        ).save()

    @classmethod
    def pay_to_wallet_before_img(cls, user_id, price):
        user_obj = Customer.objects.get(userid=user_id)
        if PaymentQueueModel.objects.filter(userid=user_obj, status=0).exists():
            PaymentQueueModel.objects.get(userid=user_obj, status=0).delete()
        PaymentQueueModel.objects.create(
            userid=user_obj,
            price=price,
            status=0,
            config_in_queue=False,
        ).save()