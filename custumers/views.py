from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import render
from .models import Customer as CustomerModel
from django.views import View
from servers.models import ConfigsInfo
from finance.models import ConfirmPaymentQueue
from servers.views import ServerApi
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


class CustomerList(LoginRequiredMixin, View):
    def get(self, request):
        customer_model = CustomerModel.objects.all()
        return render(request, 'list_custumers.html', {"customer_model": customer_model})

class CustomerDetail(LoginRequiredMixin, View):
    def get(self, request, customer_id):
        customer_obj = CustomerModel.objects.get(userid=customer_id)
        config_model = ConfigsInfo.objects.filter(chat_id=customer_obj)
        pay_model = ConfirmPaymentQueue.objects.filter(custumer=customer_obj, status=3)
        sum_pays = sum(item.price for item in pay_model)
        list_configs = []
        for i in config_model:
            config = ServerApi.get_config(i.server.server_id,i.config_name)
            config["config_name"] = i.config_name
            config["uuid"] = i.config_uuid
            list_configs.append(config)
        print(list_configs)
        return render(request, "Custumer_details.html", {"customer_obj": customer_obj, "sum_pays":sum_pays})

class GetCustumersConfigsAPI()