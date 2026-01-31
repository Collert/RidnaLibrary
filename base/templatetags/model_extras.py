from django import template
from base.enums import Genre, Theme, Tone, Audience, Language, LanguageLevel

register = template.Library()

@register.filter
def class_name(obj):
    """
    Returns the class name of an object.
    Usage: {{ loan.item|class_name }}
    """
    return obj.__class__.__name__

@register.filter
def localize_tag(tag_code):
    """
    Returns the localized name for a tag code.
    Searches through all enums (Genre, Theme, Tone, Audience, Language, LanguageLevel).
    Usage: {{ tag_code|localize_tag }}
    """
    # Build a lookup dictionary from all enums
    all_choices = {}
    for enum_class in [Genre, Theme, Tone, Audience, Language, LanguageLevel]:
        for code, label in enum_class.choices:
            all_choices[code] = label
    
    return all_choices.get(tag_code, tag_code)