from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to get item from dictionary using a key.
    Usage: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key, 0)