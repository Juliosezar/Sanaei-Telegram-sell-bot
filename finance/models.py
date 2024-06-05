from django.db import models
from custumers.models import Customer


class ConfirmPaymentQueue(models.Model):
    custumer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    price = models.PositiveIntegerField()
    pay_date = models.DateField(null=True, blank=True)
    status = models.PositiveIntegerField(default=0)
    # 0 => waiting for upload picture / 1 => waiting for confirmation / 2 => first confirme / 3 => second confirm / 10 => denied /
    config_in_queue = models.BooleanField(default=False)
    image = models.ImageField(upload_to='payment_images/', blank=True, null=True)
    deny_reseon = models.CharField(max_length=100, blank=True, null=True)
    config_uuid = models.UUIDField(unique=True, blank=True, null=True)


class Prices(models.Model):
    usage_limit = models.PositiveIntegerField()
    expire_limit = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    user_limit = models.PositiveIntegerField(default=0)
