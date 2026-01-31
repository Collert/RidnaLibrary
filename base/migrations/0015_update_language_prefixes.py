# Generated migration to update language values with new prefixes

from django.db import migrations


def update_language_prefixes(apps, schema_editor):
    """Update existing language values to include 'language_' prefix"""
    CreativeWork = apps.get_model('base', 'CreativeWork')
    
    # Mapping of old values to new values
    language_mapping = {
        'en': 'language_en',
        'fr': 'language_fr',
        'uk': 'language_uk',
    }
    
    # Update all CreativeWork objects
    for old_value, new_value in language_mapping.items():
        CreativeWork.objects.filter(language=old_value).update(language=new_value)


def reverse_language_prefixes(apps, schema_editor):
    """Reverse migration - remove 'language_' prefix"""
    CreativeWork = apps.get_model('base', 'CreativeWork')
    
    # Mapping of new values back to old values
    language_mapping = {
        'language_en': 'en',
        'language_fr': 'fr',
        'language_uk': 'uk',
    }
    
    # Update all CreativeWork objects
    for new_value, old_value in language_mapping.items():
        CreativeWork.objects.filter(language=new_value).update(language=old_value)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_alter_creativework_language_and_more'),
    ]

    operations = [
        migrations.RunPython(update_language_prefixes, reverse_language_prefixes),
    ]
