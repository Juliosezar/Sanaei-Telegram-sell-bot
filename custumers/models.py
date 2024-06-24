import uuid
from django.db import models


class Customer(models.Model):
    userid = models.PositiveBigIntegerField(primary_key=True, unique=True)
    first_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, null=True)
    wallet = models.IntegerField(default=0)
    purchase_number = models.PositiveIntegerField(default=0)
    test_config = models.BooleanField(default=False)
    temp_status = models.CharField(max_length=30, default="normal")
    pay_temp_amount = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    restrict = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name + " / " + str(self.userid)

class CustumerHistory(models.Model):
    custumer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    by_user = models.CharField(max_length=50)
    record_date = models.DateTimeField()

