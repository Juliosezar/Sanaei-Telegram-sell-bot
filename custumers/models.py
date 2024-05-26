import uuid
from servers.models import Server
from django.db import models

class Customer(models.Model):
    userid = models.IntegerField(primary_key=True, unique=True)
    first_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, null=True)
    wallet = models.IntegerField(default=0)
    purchase_number = models.PositiveIntegerField(default=0)


class Config(models.Model):
    userid = models.ForeignKey(Customer, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    config_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    config_name = models.CharField(max_length=70)
    change_location_number = models.IntegerField(default=0)
    active = models.BooleanField(default=True)


class CustumerHistory(models.Model):
    userid = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    by_user = models.CharField(max_length=50)
    record_date = models.DateTimeField()

