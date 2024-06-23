from django.db import models
from custumers.models import Customer
import uuid
from datetime import datetime


class SendMessage(models.Model):
    uuid = models.UUIDField(primary_key=True,unique=True, editable=False, default=uuid.uuid4)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(choices=
            (('Succes','Succes'), ('Created','Created'),
             ('Pending', 'Pending'), ('Faild','Faild'),
             ('Timeout','Timeout'), ('Cancelled', 'Cancelled'),
             ('Banned', 'Banned'),('Error', "Error")
             ),max_length=15, default='Created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.status + " / " + self.message[:40]