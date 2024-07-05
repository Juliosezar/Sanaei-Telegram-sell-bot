from django.shortcuts import render, redirect
from .models import ConfigLog, CustomerLog, AdminLog, CeleryDeleteConfigLog
from persiantools import jdatetime
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from finance.models import ConfirmPaymentQueue, ConfirmTamdidPaymentQueue
from django.db.models import F, Value
from connection.models import SendMessage


class Log:
    @classmethod
    def create_admin_log(cls, admin, action):
        AdminLog.objects.create(
            admin=admin,
            action=action,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        ).save()

    @classmethod
    def create_customer_log(cls, customer, action):
        CustomerLog.objects.create(
            customer=customer,
            action=action,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        ).save()

    @classmethod
    def create_config_log(cls, config, action):
        ConfigLog.objects.create(
            config=config,
            action=action,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        ).save()

    @classmethod
    def celery_delete_conf_log(cls, action, userid):
        CeleryDeleteConfigLog.objects.create(
            action=action,
            userid=userid,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        )

class AdminLogView(LoginRequiredMixin, View):
    def get(self, request):
        logs = reversed(AdminLog.objects.all())
        return render(request, "admin_logs.html", {"logs": logs})


class PaysLogView(LoginRequiredMixin, View):
    def get(self, request):
        logs1 = (ConfirmPaymentQueue.objects.filter(status__in=[1, 2, 3, 10]).order_by('-timestamp')[:100])
        logs2 = (ConfirmTamdidPaymentQueue.objects.filter(status__in=[1, 2, 3, 10]).order_by('-timestamp')[:100])
        results = (
                list(logs1.annotate(time=F('timestamp'), buy=F('id'), img=F("image")).values('time', "buy", "image")) +
                list(logs2.annotate(time=F('timestamp'), tamdid=F('id'), img=F("image")).values('time', "tamdid", "image"))
        )
        results = sorted(results, key=lambda x: x['time'], reverse=True)
        return render(request, "pay_logs.html", {"logs": results})


class CeleryDeleteConfLogView(LoginRequiredMixin, View):
    def get(self, request):
        model_obj = reversed(CeleryDeleteConfigLog.objects.all())
        return render(request, "celery_delete_conf_log.html", {"logs":model_obj})



class SendMsgsLogsView(LoginRequiredMixin, View):
    def get(self, request):
        logs = reversed(SendMessage.objects.all().order_by("updated_at"))
        return render(request, "messages_logs.html", {"logs":logs})
