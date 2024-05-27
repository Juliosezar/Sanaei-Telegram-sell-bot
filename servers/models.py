from django.db import models

class Server(models.Model):
    server_username = models.CharField(max_length=20, unique=True, primary_key=True)
    server_name = models.CharField(max_length=20)
    server_url = models.URLField(max_length=200)
    server_fake_domain = models.CharField(max_length=50, null=True)
    inbound_id = models.IntegerField()
    inbound_port = models.IntegerField()
    active = models.BooleanField(default=True)
