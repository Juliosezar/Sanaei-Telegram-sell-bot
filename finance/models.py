import uuid

from django.db import models
from custumers.models import Customer
from servers.models import ConfigsInfo


class ConfirmPaymentQueue(models.Model):
    custumer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    pay_price = models.PositiveIntegerField()
    config_price = models.PositiveIntegerField(default=0, null=True, blank=True)
    pay_date = models.DateField(null=True, blank=True)
    status = models.PositiveIntegerField(default=0)
    # 0 => waiting for upload picture / 1 => waiting for confirmation / 2 => first confirme / 3 => second confirm / 10 => denied /
    config_in_queue = models.BooleanField(default=False)
    image = models.ImageField(upload_to='payment_images/', blank=True, null=True)
    deny_reseon = models.CharField(max_length=100, blank=True, null=True)
    config_uuid = models.UUIDField(unique=True, blank=True, null=True)
    timestamp = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return str(self.custumer.userid)


class ConfirmTamdidPaymentQueue(models.Model):
    config = models.ForeignKey(ConfigsInfo, on_delete=models.CASCADE)
    pay_price = models.PositiveIntegerField()
    config_price = models.PositiveIntegerField(default=0, null=True, blank=True)
    pay_date = models.DateField(null=True, blank=True)
    status = models.PositiveIntegerField(default=0)
    # 0 => waiting for upload picture / 1 => waiting for confirmation / 2 => first confirme / 3 => second confirm / 10 => denied /
    image = models.ImageField(upload_to='payment_images/', blank=True, null=True)
    deny_reseon = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return str(self.config.config_name)


class Prices(models.Model):
    usage_limit = models.PositiveIntegerField()
    expire_limit = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    user_limit = models.PositiveIntegerField(default=0)


class OffCodes(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    type_off = models.BooleanField()  # percent = True / amount = False
    amount = models.PositiveIntegerField()
    customer_count = models.PositiveIntegerField()
    use_count = models.PositiveIntegerField()
    create_timestamp = models.PositiveBigIntegerField()
    end_timestamp = models.PositiveBigIntegerField()
    for_infinit_usages = models.BooleanField()
    for_infinit_times = models.BooleanField()
    for_not_infinity = models.BooleanField()


class UserActiveOffCodes(models.Model):
    off_code = models.ForeignKey(OffCodes, on_delete=models.CASCADE)
    custumer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    used = models.BooleanField(default=False)
