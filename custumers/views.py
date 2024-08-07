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
from rest_framework.views import APIView
from accounts.forms import SearchUserForm
from django.contrib import messages
from .forms import SendMessageToAllForm, SendMessageToCustomerForm, ChangeWalletForm, RegisterConfigToCustumerForm
from connection.models import SendMessage
from reports.models import CustomerLog

class Customer:
    @classmethod
    def create_custumer(cls, user_id, first_name, username):
        if first_name:
            first_name = first_name[:20]
        else:
            first_name = ''
        CustomerModel.objects.create(
            userid=user_id,
            first_name=first_name,
            username=username,
        ).save()


    @classmethod
    def reload_custumer_info(cls, user_id, first_name, username):
        if first_name:
            first_name = first_name[:20]
        else:
            first_name = ''
        custumer = CustomerModel.objects.get(userid=user_id)
        custumer.first_name = first_name
        custumer.username = username
        custumer.save()
# TODO

    @classmethod
    def check_custumer_info(cls, user_id, first_name, username):
        if CustomerModel.objects.filter(userid=user_id).exists():
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
        return render(request, 'list_custumers.html', {"customer_model": reversed(customer_model), 'search_user':form})

    def post(self, request):
        form = SearchUserForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data['search_user']
            customer_model = CustomerModel.objects.filter(Q(userid__icontains=word) | Q(first_name__icontains=word) | Q(username__icontains=word))
            if not customer_model.exists():
                messages.error(request, "یوزری با این مشخصات یافت نشد.")
            return render(request, 'list_custumers.html', {"customer_model": reversed(customer_model),'search_user':form})
        return redirect('accounts:home')





class CustomerDetail(LoginRequiredMixin, View):
    def get(self, request, customer_id):
        customer_obj = CustomerModel.objects.get(userid=customer_id)
        config_model = ConfigsInfo.objects.filter(chat_id=customer_obj)
        pay_model = ConfirmPaymentQueue.objects.filter(custumer=customer_obj, status=3)
        sum_pays = sum(item.pay_price for item in pay_model)
        sum_configs = True if len(config_model) > 0 else False
        
        history = reversed(CustomerLog.objects.filter(customer=customer_obj))
        return render(request, "Custumer_details.html", {"customer_obj": customer_obj, "sum_pays":sum_pays,
                            "history":history,"configs_model":config_model, "sum_configs":sum_configs})

class GetCustumersConfigsAPI(APIView):
    def get(self, request , config_uuid):
        config_model = ConfigsInfo.objects.get(config_uuid=config_uuid)
        config = ServerApi.get_config(config_model.server.server_id, config_model.config_name)
        if not config:
            return Response(status=400)
        total_usage = config["usage_limit"]
        if total_usage == 0 :
            total_usage = "&infin;"
        status = '🟢 فعال'
        if not config["started"]:
            status = "🔵 استارت نخورده"
        if not config["ended"]:
            status = "🔴 اتمام حجم یا زمان"
        hour = int((abs(config['time_expire']) % 1) * 24)
        day = abs(int(config['time_expire']))
        time_expire = f"{day}d  {hour}h"
        data = {"usage": config['usage'], "total_usage": total_usage, "time_expire": time_expire, 'status': status}
        return Response(data=data)


class SendMsgToAll(LoginRequiredMixin, View):
    def get(self, request):
        form = SendMessageToAllForm
        return render(request, 'send_msg_to_all.html', {"form": form})

    def post(self, request):
        form = SendMessageToAllForm(request.POST)
        customer_model = CustomerModel.objects.all()
        if form.is_valid():
            cd = form.cleaned_data
            if cd['all_user']:
                for i in customer_model:
                    SendMessage.objects.create(customer=i, message=cd['message'])
                return redirect('accounts:home')
            else:
                res = [eval(i) for i in cd["server"]]
                users_list = set()
                for conf in ConfigsInfo.objects.all():
                    if conf.chat_id:
                        if conf.server.server_id in res:
                            users_list.add(conf.chat_id.userid)
                for i in users_list:
                    SendMessage.objects.create(customer=CustomerModel.objects.get(userid=i), message=cd['message']).save()
                messages.success(request, "پیام شما در لیست ارسال قرار گرفت.")
                return redirect('accounts:home')
        return render(request, 'send_msg_to_all.html', {"form": form})


class SendMsgToUser(LoginRequiredMixin, View):
    def get(self, request, userid):
        form = SendMessageToCustomerForm
        return render(request, 'send_msg_to_custumer.html', {"form": form})

    def post(self, request, userid):
        form = SendMessageToAllForm(request.POST)
        customer_model = CustomerModel.objects.get(userid=userid)
        if form.is_valid():
            msg = form.cleaned_data['message']
            SendMessage.objects.create(customer=customer_model, message=msg).save()
            messages.success(request, "پیام شما در صف ارسال قرارا گرفت.")
            return redirect('customers:custumer_detail', userid)


class ChangeWalletAmount(LoginRequiredMixin, View):
    def get(self, request, userid):
        customer_model = CustomerModel.objects.get(userid=userid)
        form = ChangeWalletForm
        return render(request, "change_wallet.html", {"form": form})

    def post(self, request, userid):
        customer_model = CustomerModel.objects.get(userid=userid)
        form = ChangeWalletForm(request.POST)
        if form.is_valid():
            wallet = form.cleaned_data['wallet']
            customer_model.wallet = wallet * 1000
            customer_model.save()
            return redirect('customers:custumer_detail', userid)
        return render(request, 'change_wallet.html', {"form": form})


class UpdateCustumer(LoginRequiredMixin, View):
    def get(self, request, userid):
        from connection.command_runer import CommandRunner
        get = CommandRunner.get_user_info(userid)
        Customer.check_custumer_info(userid, get["first_name"], get["username"])
        messages.success(request, "اطلاعات یوزر آپدیت شد.")
        return redirect(request.META.get('HTTP_REFERER', '/'))


class RegisterConfigToCustumer(LoginRequiredMixin, View):
    def get(self, request, conf_uuid):
        form = RegisterConfigToCustumerForm
        config = ConfigsInfo.objects.get(config_uuid=conf_uuid)
        return render(request, "register_conf_for_customer.html", {"form": form, "config": config})

    def post(self, request, conf_uuid):
        form = RegisterConfigToCustumerForm(request.POST)
        config = ConfigsInfo.objects.get(config_uuid=conf_uuid)
        if form.is_valid():
            userid = form.cleaned_data['user_id']
            config.chat_id = CustomerModel.objects.get(userid=userid)
            config.save()
            return redirect("servers:conf_page",config.server.server_id, conf_uuid, config.config_name)
        return render(request, 'register_conf_for_customer.html', {"form": form, "config":config})


class BanUser(LoginRequiredMixin, View):
    def get(self, request, userid, status):
        from connection.command_runer import CommandRunner
        customer_model = CustomerModel.objects.get(userid=userid)
        if status == 1:
            customer_model.active = True
            CommandRunner.send_msg_to_user(userid, "✅ دسترسی شما به بات توسط ادمین مجاز شد.")
        else:
            customer_model.active = False
            CommandRunner.send_msg_to_user(userid, "⛔️ دسترسی شما به بات توسط ادمین لغو شد.")
        customer_model.save()
        return redirect("customers:custumer_detail", userid)