from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.db import models

class Genre(models.TextChoices):
    FANTASY = "fantasy", _("Fantasy")
    SCIFI = "sci_fi", _("Science Fiction")
    MYSTERY = "mystery", _("Mystery")
    THRILLER = "thriller", _("Thriller")
    ROMANCE = "romance", _("Romance")
    HORROR = "horror", _("Horror")
    BIOGRAPHY = "biography", _("Biography")
    AUTOBIOGRAPHY = "autobiography", _("Autobiography")
    HISTORY = "history", _("History")
    PHILOSOPHY = "philosophy", _("Philosophy")
    PSYCHOLOGY = "psychology", _("Psychology")
    SCIENCE = "science", _("Science")
    TECHNOLOGY = "technology", _("Technology")
    HEALTH = "health", _("Health & Fitness")
    COOKING = "cooking", _("Cooking")
    TRAVEL = "travel", _("Travel")
    SPORTS = "sports", _("Sports")
    POLITICS = "politics", _("Politics")
    ECONOMICS = "economics", _("Economics")
    RELIGION = "religion", _("Religion")
    SELF_HELP = "self_help", _("Self Help")
    BUSINESS = "business", _("Business")
    EDUCATION = "education", _("Education")
    CHILDREN = "children", _("Children's Books")
    YOUNG_ADULT = "young_adult", _("Young Adult")
    POETRY = "poetry", _("Poetry")
    DRAMA = "drama", _("Drama")
    CLASSICS = "classics", _("Classics")
    CONTEMPORARY = "contemporary", _("Contemporary Fiction")
    HISTORICAL_FICTION = "historical_fiction", _("Historical Fiction")
    CRIME = "crime", _("Crime")
    ADVENTURE = "adventure", _("Adventure")
    HUMOR = "humor", _("Humor")
    ARTS = "arts", _("Arts & Music")
    REFERENCE = "reference", _("Reference")
    OTHER = "other", _("Other")

    @classmethod
    def get_genre_counts(cls):
        """Return a dictionary with genre codes as keys and item counts as values"""
        from .models import CreativeWork  # Import here to avoid circular dependency
        
        # Get all genre choices
        genre_dict = {choice[0]: 0 for choice in cls.choices}
        
        # Query creative works grouped by genre
        genre_counts = CreativeWork.objects.values('genre').annotate(count=Count('id'))
        
        # Update the dictionary with actual counts
        for entry in genre_counts:
            if entry['genre'] in genre_dict:
                genre_dict[entry['genre']] = entry['count']
        
        return genre_dict
    
    @classmethod
    def choices_with_counts(cls):
        """Return a list of genres with their counts for display purposes"""
        genre_counts = cls.get_genre_counts()
        genres_list = []
        for code, name in cls.choices:
            genres_list.append({
                'code': code,
                'name': name,
                'count': genre_counts.get(code, 0)
            })
        return genres_list

class Language(models.TextChoices):
    ENGLISH    = "en", _("English")
    FRENCH     = "fr", _("French")
    UKRAINIAN  = "uk", _("Ukrainian")

    @classmethod
    def get_language_counts(cls):
        """Return a dictionary with language codes as keys and item counts as values"""
        from .models import CreativeWork  # Import here to avoid circular dependency
        
        # Get all language choices
        language_dict = {choice[0]: 0 for choice in cls.choices}
        
        # Query creative works grouped by language
        language_counts = CreativeWork.objects.values('language').annotate(count=Count('id'))
        
        # Update the dictionary with actual counts
        for entry in language_counts:
            if entry['language'] in language_dict:
                language_dict[entry['language']] = entry['count']
        
        return language_dict
    
    @classmethod
    def choices_with_counts(cls):
        """Return a list of languages with their counts for display purposes"""
        language_counts = cls.get_language_counts()
        languages_list = []
        for code, name in cls.choices:
            languages_list.append({
                'code': code,
                'name': name,
                'count': language_counts.get(code, 0)
            })
        return languages_list
    
class Theme(models.TextChoices):
    LOVE = "love", _("Love & Romance")
    BETRAYAL = "betrayal", _("Betrayal")
    REDEMPTION = "redemption", _("Redemption")
    COMING_OF_AGE = "coming_of_age", _("Coming of Age")
    GOOD_VS_EVIL = "good_vs_evil", _("Good vs Evil")
    IDENTITY = "identity", _("Identity & Self-Discovery")
    SURVIVAL = "survival", _("Survival")
    FAMILY = "family", _("Family & Relationships")
    FRIENDSHIP = "friendship", _("Friendship & Loyalty")
    POWER_CORRUPTION = "power_corruption", _("Power & Corruption")
    REVENGE = "revenge", _("Revenge")
    SACRIFICE = "sacrifice", _("Sacrifice")
    FREEDOM = "freedom", _("Freedom & Liberation")
    JUSTICE = "justice", _("Justice & Morality")
    WAR = "war", _("War & Conflict")
    DEATH_MORTALITY = "death_mortality", _("Death & Mortality")
    HOPE = "hope", _("Hope & Perseverance")
    FAITH_SPIRITUALITY = "faith_spirituality", _("Faith & Spirituality")
    SOCIAL_CLASS = "social_class", _("Social Class & Inequality")
    PREJUDICE = "prejudice", _("Prejudice & Discrimination")
    LOSS_GRIEF = "loss_grief", _("Loss & Grief")
    TRANSFORMATION = "transformation", _("Transformation & Change")
    DESTINY_FATE = "destiny_fate", _("Destiny & Fate")
    ISOLATION = "isolation", _("Isolation & Loneliness")
    COURAGE = "courage", _("Courage & Heroism")

    @classmethod
    def get_theme_counts(cls):
        """Return a dictionary with theme codes as keys and item counts as values"""
        from .models import CreativeWork  # Import here to avoid circular dependency
        
        # Get all theme choices
        theme_dict = {choice[0]: 0 for choice in cls.choices}
        
        # Query creative works grouped by theme
        theme_counts = CreativeWork.objects.values('theme').annotate(count=Count('id'))
        
        # Update the dictionary with actual counts
        for entry in theme_counts:
            if entry['theme'] in theme_dict:
                theme_dict[entry['theme']] = entry['count']
        
        return theme_dict
    
    @classmethod
    def choices_with_counts(cls):
        """Return a list of themes with their counts for display purposes"""
        theme_counts = cls.get_theme_counts()
        themes_list = []
        for code, name in cls.choices:
            themes_list.append({
                'code': code,
                'name': name,
                'count': theme_counts.get(code, 0)
            })
        return themes_list

class Tone(models.TextChoices):
    LIGHT = "light", _("Light & Humorous")
    DARK = "dark", _("Dark & Serious")
    SATIRICAL = "satirical", _("Satirical & Ironic")
    ROMANTIC = "romantic", _("Romantic & Sentimental")
    MYSTERIOUS = "mysterious", _("Mysterious & Suspenseful")
    OPTIMISTIC = "optimistic", _("Optimistic & Uplifting")
    PESSIMISTIC = "pessimistic", _("Pessimistic & Bleak")
    WHIMSICAL = "whimsical", _("Whimsical & Fantastical")
    NOSTALGIC = "nostalgic", _("Nostalgic & Reflective")
    SERENE = "serene", _("Serene & Peaceful")

    @classmethod
    def get_tone_counts(cls):
        """Return a dictionary with tone codes as keys and item counts as values"""
        from .models import CreativeWork  # Import here to avoid circular dependency
        
        # Get all tone choices
        tone_dict = {choice[0]: 0 for choice in cls.choices}
        
        # Query items grouped by tone
        tone_counts = CreativeWork.objects.values('tone').annotate(count=Count('id'))
        
        # Update the dictionary with actual counts
        for entry in tone_counts:
            if entry['tone'] in tone_dict:
                tone_dict[entry['tone']] = entry['count']
        
        return tone_dict
    
    @classmethod
    def choices_with_counts(cls):
        """Return a list of tones with their counts for display purposes"""
        tone_counts = cls.get_tone_counts()
        tones_list = []
        for code, name in cls.choices:
            tones_list.append({
                'code': code,
                'name': name,
                'count': tone_counts.get(code, 0)
            })
        return tones_list

class Audience(models.TextChoices):
    CHILDREN = "children", _("Children")
    YOUNG_ADULT = "young_adult", _("Young Adult")
    ADULT = "adult", _("Adult")
    GENERAL = "general", _("General Audience")

    @classmethod
    def get_audience_counts(cls):
        """Return a dictionary with audience codes as keys and item counts as values"""
        from .models import CreativeWork  # Import here to avoid circular dependency
        
        # Get all audience choices
        audience_dict = {choice[0]: 0 for choice in cls.choices}
        
        # Query items grouped by audience
        audience_counts = CreativeWork.objects.values('audience').annotate(count=Count('id'))
        
        # Update the dictionary with actual counts
        for entry in audience_counts:
            if entry['audience'] in audience_dict:
                audience_dict[entry['audience']] = entry['count']
        
        return audience_dict
    
    @classmethod
    def choices_with_counts(cls):
        """Return a list of audiences with their counts for display purposes"""
        audience_counts = cls.get_audience_counts()
        audiences_list = []
        for code, name in cls.choices:
            audiences_list.append({
                'code': code,
                'name': name,
                'count': audience_counts.get(code, 0)
            })
        return audiences_list
    
class LanguageLevel(models.TextChoices):
    BEGINNER = "beginner", _("Beginner")
    INTERMEDIATE = "intermediate", _("Intermediate")
    ADVANCED = "advanced", _("Advanced")
    EXPERT = "expert", _("Expert")

    @classmethod
    def get_language_level_counts(cls):
        """Return a dictionary with language level codes as keys and item counts as values"""
        from .models import CreativeWork  # Import here to avoid circular dependency
        
        # Get all language level choices
        language_level_dict = {choice[0]: 0 for choice in cls.choices}
        
        # Query items grouped by language level
        language_level_counts = CreativeWork.objects.values('language_level').annotate(count=Count('id'))
        
        # Update the dictionary with actual counts
        for entry in language_level_counts:
            if entry['language_level'] in language_level_dict:
                language_level_dict[entry['language_level']] = entry['count']
        
        return language_level_dict
    
    @classmethod
    def choices_with_counts(cls):
        """Return a list of language levels with their counts for display purposes"""
        language_level_counts = cls.get_language_level_counts()
        language_levels_list = []
        for code, name in cls.choices:
            language_levels_list.append({
                'code': code,
                'name': name,
                'count': language_level_counts.get(code, 0)
            })
        return language_levels_list