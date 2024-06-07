import datetime
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from rest_framework.response import Response
from .models import Customer as CustomerModel
from django.views import View
from servers.models import ConfigsInfo
from finance.models import ConfirmPaymentQueue
from servers.views import ServerApi
from binary import BinaryUnits, convert_units
from rest_framework.views import APIView
from accounts.forms import SearchUserForm
from django.contrib import messages
from .forms import SendMessageForm
from connection import tasks
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
        form = SearchUserForm()
        return render(request, 'list_custumers.html', {"customer_model": customer_model, 'search_user':form})

    def post(self, request):
        form = SearchUserForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data['search_user']
            customer_model = CustomerModel.objects.filter(Q(userid__icontains=word) | Q(first_name__icontains=word) | Q(username__icontains=word))
            if not customer_model.exists():
                messages.error(request, "یوزری با این مشخصات یافت نشد.")
            return render(request, 'list_custumers.html', {"customer_model": customer_model,'search_user':form})
        return redirect('accounts:home')





class CustomerDetail(LoginRequiredMixin, View):
    def get(self, request, customer_id):
        customer_obj = CustomerModel.objects.get(userid=customer_id)
        config_model = ConfigsInfo.objects.filter(chat_id=customer_obj)
        pay_model = ConfirmPaymentQueue.objects.filter(custumer=customer_obj, status=3)
        sum_pays = sum(item.price for item in pay_model)
        sum_configs = True if len(config_model) > 0 else False
        return render(request, "Custumer_details.html", {"customer_obj": customer_obj, "sum_pays":sum_pays,
                                            "configs_model":config_model, "sum_configs":sum_configs})

class GetCustumersConfigsAPI(APIView):
    def get(self, request , config_uuid):
        config_model = ConfigsInfo.objects.get(config_uuid=config_uuid)
        config = ServerApi.get_config(config_model.server.server_id, config_model.config_name)
        if not config:
            return Response(status=400)
        presentDate = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(presentDate) * 1000
        time_expire = config["expiryTime"]
        expired = False
        started = True
        if time_expire > 0:
            time_expire = int((time_expire - unix_timestamp) / 86400000)
            if time_expire < 0:
                expired = True
                time_expire = abs(time_expire)
        elif time_expire == 0:
            time_expire = "&infin;"
            if config['usage'] == 0:
                started = False
        else:
            time_expire = abs(int(time_expire / 86400000))
            started = False
        usage = config['usage']
        usage = round(convert_units(usage, BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
        total_usage = config["usage_limit"]
        total_usage = int(convert_units(total_usage, BinaryUnits.BYTE, BinaryUnits.GB)[0])
        if total_usage == 0 :
            total_usage = "&infin;"
        status = '🟢 فعال'
        if not started:
            status = "🔵 استارت نخورده"
        if not config["enable"]:
            status = "🔴 اتمام حجم یا زمان"
        print(config["enable"])
        data = {"usage": usage, "total_usage": total_usage, "time_expire": time_expire, 'status': status}
        return Response(data=data)


class SendMsgToAll(LoginRequiredMixin, View):
    def get(self, request):
        form = SendMessageForm
        return render(request, 'send_msg_to_all.html', {"form": form})

    def post(self, request):
        form = SendMessageForm(request.POST)
        customer_model = CustomerModel.objects.all()
        if form.is_valid():
            cd = form.cleaned_data
            if cd['all_user']:
                for i in customer_model:
                    tasks.send_msg_to_bot.apply_async(args=[i.userid, cd["message"]])
        return redirect('accounts:home')