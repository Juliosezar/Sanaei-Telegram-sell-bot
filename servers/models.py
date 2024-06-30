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
    iphone = models.BooleanField(default=False)

    def __str__(self):
        return self.server_name

class ConfigsInfo(models.Model):
    config_name = models.CharField(max_length=25, unique=True)
    config_uuid = models.UUIDField(unique=True)
    server = models.ForeignKey(Server, on_delete=models.DO_NOTHING)
    chat_id = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, null=True)
    price = models.PositiveIntegerField(default=0)
    paid = models.BooleanField(default=True)
    created_by = models.CharField(max_length=20, default="BOT")
    renew_count = models.IntegerField(default=0)
    change_location_time = models.IntegerField(default=0)


    def __str__(self):
        return self.config_name


class CreateConfigQueue(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    custumer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    config_uuid = models.UUIDField(unique=True)
    config_name = models.CharField(max_length=50, unique=True)
    usage_limit = models.IntegerField()
    expire_time = models.IntegerField()
    user_limit = models.IntegerField()
    price = models.IntegerField()
    sent_to_user = models.IntegerField(default=0)
    # 0 = Created    1 = pending server   2 = sent  5 = Faild
    pay_status = models.PositiveSmallIntegerField(default=0)
    # 0 => waiting for pay img / 1 => waiting for confirm / 2 => first confirmed / 3 => secoend confirm / 10 => denied

    def __str__(self):
        return self.config_name

class TamdidConfigQueue(models.Model):
    config = models.ForeignKey(ConfigsInfo, on_delete=models.CASCADE)
    usage_limit = models.IntegerField()
    expire_time = models.IntegerField()
    user_limit = models.IntegerField()
    price = models.IntegerField()
    sent_to_user = models.IntegerField(default=0)
    # 0 = Created    1 = pending server   2 = sent  5 = Faild
    pay_status = models.PositiveSmallIntegerField(default=0)
    # 0 => waiting for pay img / 1 => waiting for confirm / 2 => first confirmed / 3 => secoend confirm / 10 => denied

    def __str__(self):
        return self.config.config_name


class MsgEndOfConfig(models.Model):
    config = models.OneToOneField(ConfigsInfo, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    almost_time = models.BooleanField(default=False)
    almost_usage = models.BooleanField(default=False)
    ended_time = models.BooleanField(default=False)
    ended_usage = models.BooleanField(default=False)


class InfinitCongisLimit(models.Model):
    config = models.OneToOneField(ConfigsInfo, on_delete=models.CASCADE)
    limit = models.IntegerField()






