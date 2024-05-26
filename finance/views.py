from django.shortcuts import render
from .models import Payment
from custumers.models import Customer

class Wallet:
    @classmethod
    def get_wallet_anount(cls, user_id):
        amount = Customer.objects.get(userid=user_id).wallet
        return amount
