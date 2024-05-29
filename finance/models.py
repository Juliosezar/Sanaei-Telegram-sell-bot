from django.db import models
from custumers.models import Customer

class Payment(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    amount = models.PositiveIntegerField()
    pay_date = models.DateField()
    status = models.PositiveIntegerField(default=0)
    # 0 => waiting for confirmation / 1 => confirme / 2 => denied / 3 => waiting for upload picture
    config_in_queue = models.BooleanField(default=False)
    image = models.ImageField(upload_to='media/', blank=True, null=True)



class Prices(models.Model):
    usage_limit = models.PositiveIntegerField()
    expire_limit = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    user_limit = models.PositiveIntegerField(default=0)