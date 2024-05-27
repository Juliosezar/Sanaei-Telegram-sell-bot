from django.shortcuts import render
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

