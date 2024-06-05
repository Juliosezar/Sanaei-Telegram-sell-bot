from django import template

register = template.Library()


@register.filter
def price(amount):
    return f"{amount:,}"




@register.filter(name='percent')
def percent_usage(value, arg):
    return int(value / arg * 100)