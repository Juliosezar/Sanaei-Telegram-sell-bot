from django.db import models

class Customer(models.Model):
    userid = models.IntegerField(primary_key=True, unique=True)
    chatid = models.IntegerField(primary_key=True, unique=True)
    first_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)


