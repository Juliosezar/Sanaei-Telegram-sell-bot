from django.contrib import admin
from .models import Server, ConfigsInfo,CreateConfigQueue, TamdidConfigQueue

admin.site.register(Server)
admin.site.register(ConfigsInfo)
admin.site.register(CreateConfigQueue)
admin.site.register(TamdidConfigQueue)
