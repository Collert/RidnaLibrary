from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from parler.models import TranslatableModel, TranslatedFields

def calculate_next_saturday():
    today = timezone.now().date()
    days_ahead = 5 - today.weekday()  # Saturday is 5
    if days_ahead <= 0:
        days_ahead += 7
    return days_ahead

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

class Language(models.TextChoices):
    ENGLISH    = "en", _("English")
    FRENCH     = "fr", _("French")
    UKRAINIAN  = "uk", _("Ukrainian")

class Item(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    title_fr = models.CharField(max_length=200, blank=True)
    author_fr = models.CharField(max_length=100, blank=True)
    description_fr = models.TextField(blank=True)
    title_uk = models.CharField(max_length=200, blank=True)
    author_uk = models.CharField(max_length=100, blank=True)
    description_uk = models.TextField(blank=True)
    published_date = models.DateField()
    language = models.CharField(max_length=10, default='en', choices=Language.choices)
    genre = models.CharField(max_length=50, choices=Genre.choices)
    total_copies = models.PositiveIntegerField(default=1)
    added_date = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    favourited_by = models.ManyToManyField(User, related_name='favourite_items', blank=True)

    def __str__(self):
        return self.title
    
    def is_available(self):
        return Loan.objects.filter(item=self, return_date__isnull=True).count() < self.total_copies

    def available_copies(self):
        loaned_copies = Loan.objects.filter(item=self, return_date__isnull=True).count()
        return self.total_copies - loaned_copies
    
    def is_borrowed_by(self, user):
        return Loan.objects.filter(item=self, user=user, return_date__isnull=True, received=True).exists()
    
    def is_borrowed_and_not_received_by(self, user):
        return Loan.objects.filter(item=self, user=user, return_date__isnull=True, received=False).exists()

    def get_localized_author(self):
        """Return the author name in the current language"""
        current_language = get_language()
        if current_language == 'uk' and self.author_uk:
            return self.author_uk
        elif current_language == 'fr' and self.author_fr:
            return self.author_fr
        else:
            return self.author

    def get_localized_title(self):
        """Return the title in the current language"""
        current_language = get_language()
        if current_language == 'uk' and self.title_uk:
            return self.title_uk
        elif current_language == 'fr' and self.title_fr:
            return self.title_fr
        else:
            return self.title

    def get_localized_description(self):
        """Return the description in the current language"""
        current_language = get_language()
        if current_language == 'uk' and self.description_uk:
            return self.description_uk
        elif current_language == 'fr' and self.description_fr:
            return self.description_fr
        else:
            return self.description
    
    def new_arrivals(self):
        return self.objects.all().order_by('-added_date')[:15]
    
    def users_position_in_hold_queue(self, user):
        holds = self.holds.filter(item=self).order_by('hold_date')
        for position, hold in enumerate(holds, start=1):
            if hold.user == user:
                return position
        return None
    
    def borrow_queue(self):
        return self.holds.filter(item=self).order_by('hold_date')

class Book(Item):
    isbn_number = models.CharField(max_length=13, unique=True)

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    join_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name and self.user.last_name else self.user.username
    
    @receiver(post_save, sender=User)
    def create_member_profile(sender, instance, created, **kwargs):
        if created:
            Member.objects.create(user=instance)

class Loan(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_date = models.DateField(default=timezone.now() + timedelta(days=calculate_next_saturday()))
    received = models.BooleanField(default=False)
    return_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(default=timezone.now() + timedelta(days=calculate_next_saturday()) + timedelta(days=14))
    unlimited_loan = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item.title} loaned to {self.user.username}"
    
    def days_left(self):
        return (self.due_date - timezone.now().date() - timedelta(days=17)).days
    
    def rounded_percent_loan_progress(self):
        total_loan_period = (self.due_date - self.loan_date).days
        days_left = self.days_left()
        progress_percent = 100 - (days_left / total_loan_period) * 100
        return min([10, 20, 40, 60, 80, 90], key=lambda x: abs(x - progress_percent))

    def is_overdue(self):
        return not self.unlimited_loan and not self.return_date and self.days_left() < 0

    def days_overdue(self):
        if self.is_overdue():
            return abs(self.days_left())
        return 0
    

class HeroSection(models.Model):
    title = models.CharField(max_length=50)
    image = models.ImageField(upload_to='hero_images/')
    button_text = models.CharField(max_length=10)
    button_link = models.URLField()

    def __str__(self):
        return self.title

class FeaturedItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"Featured: {self.item.title}"
    
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateTimeField()

    def __str__(self):
        return self.title
    
class ItemHold(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='holds')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hold_date = models.DateField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"Hold: {self.item.title} for {self.user.username}"