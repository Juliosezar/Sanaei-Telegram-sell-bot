from django import template
from servers.models import ConfigsInfo, InfinitCongisLimit
from django.conf import settings
import json
from persiantools.jdatetime import JalaliDateTime
import datetime, pytz
from servers.models import CreateConfigQueue

register = template.Library()

with open(settings.BASE_DIR / "settings.json", "r") as f:
    data = json.load(f)
    IP1 = data["one_usage_limit"]
    IP2 = data["two_usage_limit"]
    IP3 = data["three_usage_limit"]

@register.filter
def price(amount):
    return f"{amount:,}"




@register.filter(name='percent')
def percent_usage(value, arg):
    return int(value / arg * 100)

@register.filter(name="dh")
def day_and_hour(value):
    hour = int((abs(value) % 1) * 24)
    day = abs(int(value))
    return f"{day}d  {hour}h"


@register.filter(name="break_name")
def break_name(value):
    if ConfigsInfo.objects.filter(config_name=value).exists():
        return f'{value} 🤖'
    elif '@' in value:
        return False
    return value

@register.filter(name="config_seved")
def config_seved(value):
    if ConfigsInfo.objects.filter(config_uuid=value).exists():
        return True
    return False


@register.filter(name="infinit_limit")
def infinit_limit(value, ip_limit):
    config_info = ConfigsInfo.objects.filter(config_uuid=value)
    if config_info.exists():
        if InfinitCongisLimit.objects.filter(config__config_uuid=value).exists():
            return InfinitCongisLimit.objects.get(config_name=value).limit
        else:
            if ip_limit == 1:
                return IP1
            elif ip_limit == 2:
                return IP2
            elif ip_limit == 3:
                return IP3
            else:
                return 0
    return None



@register.filter(name="timestamp")
def timestamp(value):
    return JalaliDateTime.fromtimestamp(value, pytz.timezone("Asia/Tehran")).strftime("%c")


@register.filter(name="get_server")
def get_server(value):
    if CreateConfigQueue.objects.filter(config_uuid=value).exists():
        return CreateConfigQueue.objects.get(config_uuid=value).server.server_name
    else:
        return "----"


