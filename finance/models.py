from django.db import models
from custumers.models import Customer
class Payment(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    amount = models.PositiveIntegerField()
    pay_date = models.DateField()
    confirmation = models.PositiveIntegerField(default=0)
    # 0 => waiting for confirmation / 1 => confirme / 2 => denied
    deny_reason = models.CharField(default='', max_length=100)
    config_in_queue = models.BooleanField(default=False)


class Prices(models.Model):
    usage_limit = models.PositiveIntegerField()
    expire_limit = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
