from django.shortcuts import render
from .models import Customer as CustomerModel
class Customer:

    @classmethod
    def create_custumer(cls, user_id, first_name, username):
        CustomerModel.objects.create(
            userid=user_id,
            first_name=first_name,
            username=username,
        ).save()
        print("created")

    @classmethod
    def reload_custumer_info(cls, user_id, first_name, username):
        custumer = CustomerModel.objects.get(userid=user_id)
        custumer.first_name = first_name
        custumer.username = username
        custumer.save()
        print("edited")
# TODO

    @classmethod
    def check_custumer_info(cls, user_id, first_name, username):
        user = CustomerModel.objects.filter(userid=user_id)
        if user.exists():
            user = CustomerModel.objects.get(userid=user_id)
            if not (user.first_name == first_name and user.username == username):
                cls.reload_custumer_info(user_id, first_name, username)
        else:
            cls.create_custumer(user_id, first_name, username)
            return False
        return True
# TODO

    @classmethod
    def change_custimer_temp_status(cls, user_id, status):
        custumer_obj = CustomerModel.objects.get(userid=user_id)
        custumer_obj.temp_status = status
        custumer_obj.save()
