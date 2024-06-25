from django.contrib import admin
from .models import SendMessage, EndOfConfigCounter

admin.site.register(SendMessage)
admin.site.register(EndOfConfigCounter)
