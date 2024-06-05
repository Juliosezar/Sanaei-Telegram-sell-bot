from django import template

register = template.Library()


@register.filter
def price(amount):
    return f"{amount:,}"
