from django.shortcuts import render, redirect
from .models import ConfigLog, CustomerLog, AdminLog
from persiantools import jdatetime
class Log:
    @staticmethod
    def create_admin_log(cls, admin, action):
        AdminLog.objects.create(
            admin=admin,
            action=action,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        ).save()

    def create_customer_log(cls, customer, action):
        CustomerLog.objects.create(
            customer=customer,
            action=action,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        ).save()


    def create_config_log(cls, admin, action):
        AdminLog.objects.create(
            admin=admin,
            action=action,
            timestamp=int(jdatetime.JalaliDateTime.now().timestamp())
        ).save()