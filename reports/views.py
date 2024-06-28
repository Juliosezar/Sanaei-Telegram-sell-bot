from django.shortcuts import render, redirect
from .models import ConfigLog, CustomerLog, AdminLog
from persiantools import jdatetime
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

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


class AdminLogView(LoginRequiredMixin, View):
    def get(self, request):
        logs = reversed(AdminLog.objects.all())
        return render(request, "admin_logs.html", {"logs": logs})