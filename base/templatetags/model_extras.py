from django import template

register = template.Library()

@register.filter
def class_name(obj):
    """
    Returns the class name of an object.
    Usage: {{ loan.item|class_name }}
    """
    return obj.__class__.__name__