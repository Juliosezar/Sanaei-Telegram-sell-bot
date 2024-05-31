import uuid
from custumers.models import Customer
from django.db import models

class Server(models.Model):
    server_id = models.IntegerField(unique=True, primary_key=True)
    server_name = models.CharField(max_length=20)
    server_url = models.URLField(max_length=200)
    username = models.CharField(max_length=30, null=True)
    password = models.CharField(max_length=40, null=True)
    server_fake_domain = models.CharField(max_length=50, null=True)
    inbound_id = models.IntegerField()
    inbound_port = models.IntegerField()
    active = models.BooleanField(default=True)



class CreateConfigQueue(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    custumer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    config_uuid = models.UUIDField(unique=True)
    config_name = models.CharField(max_length=50, unique=True)
    usage_limit = models.IntegerField()
    expire_time = models.IntegerField()
    user_limit = models.IntegerField()
    price = models.IntegerField()
    sent_to_user = models.BooleanField(default=False)
    pay_status = models.PositiveSmallIntegerField(default=0)
    # 0 => waiting for pay img / 1 => waiting for confirm / 2 => confirmed / 3 => secoend confirm / 10 => denied
