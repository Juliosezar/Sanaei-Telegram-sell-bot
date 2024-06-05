from django import template

register = template.Library()


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
    if '@' in value:
        return f'{value.split('@')[1]}🔒'
    return value
