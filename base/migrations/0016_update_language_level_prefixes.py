# Generated migration to update language level values with new suffixes

from django.db import migrations


def update_language_level_suffixes(apps, schema_editor):
    """Update existing language level values to include '_reading_level' suffix"""
    CreativeWork = apps.get_model('base', 'CreativeWork')
    
    # Mapping of old values to new values
    language_level_mapping = {
        'beginner': 'beginner_reading_level',
        'intermediate': 'intermediate_reading_level',
        'advanced': 'advanced_reading_level',
        'expert': 'expert_reading_level',
    }
    
    # Update all CreativeWork objects
    for old_value, new_value in language_level_mapping.items():
        CreativeWork.objects.filter(language_level=old_value).update(language_level=new_value)


def reverse_language_level_suffixes(apps, schema_editor):
    """Reverse migration - remove '_reading_level' suffix"""
    CreativeWork = apps.get_model('base', 'CreativeWork')
    
    # Mapping of new values back to old values
    language_level_mapping = {
        'beginner_reading_level': 'beginner',
        'intermediate_reading_level': 'intermediate',
        'advanced_reading_level': 'advanced',
        'expert_reading_level': 'expert',
    }
    
    # Update all CreativeWork objects
    for new_value, old_value in language_level_mapping.items():
        CreativeWork.objects.filter(language_level=new_value).update(language_level=old_value)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_update_language_prefixes'),
    ]

    operations = [
        migrations.RunPython(update_language_level_suffixes, reverse_language_level_suffixes),
    ]
