from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from servers.models import Server, ConfigsInfo, InfinitCongisLimit, TestConfig
from .models import ConfigLog, CustomerLog, AdminLog, CeleryDeleteConfigLog
from persiantools import jdatetime
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from finance.models import ConfirmPaymentQueue, ConfirmTamdidPaymentQueue
from django.db.models import F, Value, Sum
from connection.models import SendMessage
from custumers.models import Customer
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response

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
                list(logs2.annotate(time=F('timestamp'), tamdid=F('id'), img=F("image")).values('time', "tamdid",
                                                                                                "image"))
        )
        results = sorted(results, key=lambda x: x['time'], reverse=True)
        return render(request, "pay_logs.html", {"logs": results})


class CeleryDeleteConfLogView(LoginRequiredMixin, View):
    def get(self, request):
        model_obj = reversed(CeleryDeleteConfigLog.objects.all())
        return render(request, "celery_delete_conf_log.html", {"logs": model_obj})


class SendMsgsLogsView(LoginRequiredMixin, View):
    def get(self, request):
        logs = reversed(SendMessage.objects.all().order_by("updated_at"))
        return render(request, "messages_logs.html", {"logs": logs})


class DeleteMsgView(LoginRequiredMixin, View):
    def get(self, request, typ):
        if typ == "Succes":
            SendMessage.objects.filter(status="Succes").delete()
        elif typ == "Failure":
            SendMessage.objects.filter(status__in=["Error", "Faild", "Timeout", "Banned"]).delete()
        return redirect("reports:send_msgs_log")



class ReportsView(LoginRequiredMixin, View):
    def get(self, request):

        custumers_count = Customer.objects.count()
        wallet_sum = Customer.objects.aggregate(Sum('wallet'))["wallet__sum"]
        baned_user = Customer.objects.filter(active=False).count()

        configs_count = ConfigLog.objects.count()
        server_confs_count = {}
        for i in Server.objects.all(): server_confs_count[i] = 0
        for config in ConfigsInfo.objects.all():
            server_confs_count[config.server] += 1
        infinitconfs_count = InfinitCongisLimit.objects.count()
        testconfs_count = TestConfig.objects.count()
        now = int(jdatetime.JalaliDateTime.now().timestamp())
        one_month_ago_time = int(jdatetime.JalaliDateTime.now().timestamp()) - 2629800
        one_day_ago_time = int(jdatetime.JalaliDateTime.now().timestamp()) - 86400
        one_week_ago_time = int(jdatetime.JalaliDateTime.now().timestamp()) - 604800
        buys_count_all_time = ConfirmPaymentQueue.objects.filter(status__in=[2, 3]).count()
        tamdids_count_all_time = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3]).count()
        buys_price_all_time = ConfirmPaymentQueue.objects.filter(status__in=[2, 3]).aggregate(Sum("pay_price"))[
                                  "pay_price__sum"] or 0
        tamdids_price_all_time = \
        ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3]).aggregate(Sum("pay_price"))["pay_price__sum"] or 0
        deny_pays_count_all_time = ConfirmPaymentQueue.objects.filter(
            status=10).count() + ConfirmTamdidPaymentQueue.objects.filter(status=10).count()

        buys_count_last_month = ConfirmPaymentQueue.objects.filter(status__in=[2, 3],
                                                                   timestamp__range=(one_month_ago_time, now)).count()
        tamdids_count_last_month = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(
        one_month_ago_time, now)).count()
        buys_price_last_month = \
        ConfirmPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(one_month_ago_time, now)).aggregate(
            Sum("pay_price"))["pay_price__sum"] or 0
        tamdids_price_last_month = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(
        one_month_ago_time, now)).aggregate(Sum("pay_price"))["pay_price__sum"] or 0
        deny_pays_count_last_month = ConfirmPaymentQueue.objects.filter(status=10, timestamp__range=(
        one_month_ago_time, now)).count() + ConfirmTamdidPaymentQueue.objects.filter(status=10, timestamp__range=(
        one_month_ago_time, now)).count()

        buys_count_last_week = ConfirmPaymentQueue.objects.filter(status__in=[2, 3],
                                                                  timestamp__range=(one_week_ago_time, now)).count()
        tamdids_count_last_week = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(
        one_week_ago_time, now)).count()
        buys_price_last_week = \
        ConfirmPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(one_week_ago_time, now)).aggregate(Sum("pay_price"))["pay_price__sum"] or 0
        tamdids_price_last_week = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(
        one_week_ago_time, now)).aggregate(Sum("pay_price"))["pay_price__sum"] or 0

        buys_count_last_day = ConfirmPaymentQueue.objects.filter(status__in=[2, 3],timestamp__range=(one_day_ago_time, now)).count()
        tamdids_count_last_day = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(
        one_day_ago_time, now)).count()
        buys_price_last_day = \
        ConfirmPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(one_day_ago_time, now)).aggregate(
            Sum("pay_price"))["pay_price__sum"] or 0
        tamdids_price_last_day = \
        ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(one_day_ago_time, now)).aggregate(
            Sum("pay_price"))["pay_price__sum"] or 0

        data = {"custumers_count": custumers_count, "wallet_sum": wallet_sum, "baned_user": baned_user,
                "configs_count": configs_count,
                "server_confs_count": server_confs_count, "testconfs_count": testconfs_count,
                "infinitconfs_count": infinitconfs_count, "buys_count_all_time": buys_count_all_time,
                "tamdids_count_all_time": tamdids_count_all_time, "buys_count_last_month": buys_count_last_month,
                "tamdids_count_last_month": tamdids_count_last_month, "buys_price_last_month": buys_price_last_month,
                "tamdids_price_last_month": tamdids_price_last_month, "buys_count_last_week": buys_count_last_week,
                "tamdids_count_last_week": tamdids_count_last_week, "buys_price_last_week": buys_price_last_week,
                "tamdids_price_last_week": tamdids_price_last_week, "buys_count_last_day": buys_count_last_day,
                "buys_price_all_time": buys_price_all_time, "tamdids_price_all_time": tamdids_price_all_time,
                "deny_pays_count_last_month": deny_pays_count_last_month,
                "deny_pays_count_all_time": deny_pays_count_all_time,
                "tamdids_count_last_day": tamdids_count_last_day, "tamdids_price_last_day": tamdids_price_last_day,
                "buys_price_last_day": buys_price_last_day
                }

        return render(request, "reports.html", data)



class ChartData(APIView):
    def get(self, request, format=None):
        now = int(jdatetime.JalaliDateTime.now().timestamp())
        chartdata = []
        for week in range(0, 27):
            start = now - (week * 604800)
            end = now - ((week + 1) * 604800)
            buy = ConfirmPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(end, start)).count()
            tamdid = ConfirmTamdidPaymentQueue.objects.filter(status__in=[2, 3], timestamp__range=(end, start)).count()
            chartdata.insert(0, buy+tamdid)
        labels = [
            "Now"
        ]
        for i in range(1,27):
            labels.insert(0, str(i))
        chartLabel = "بر اساس تعداد خرید و تمدید / هفته"

        data = {
            "labels": labels,
            "chartLabel": chartLabel,
            "chartdata": chartdata,
        }
        return Response(data)
