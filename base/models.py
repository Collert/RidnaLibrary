from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

def calculate_next_saturday():
    today = timezone.now().date()
    days_ahead = 5 - today.weekday()  # Saturday is 5
    if days_ahead <= 0:
        days_ahead += 7
    return days_ahead

class Item(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    published_date = models.DateField()
    added_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def is_available(self):
        return not Loan.objects.filter(book=self, return_date__isnull=True).exists()
    
    def available_copies(self):
        total_copies = self.objects.filter(title=self.title).count()
        loaned_copies = Loan.objects.filter(book__title=self.title, return_date__isnull=True).count()
        return total_copies - loaned_copies
    
    def new_arrivals(self):
        return self.objects.all().order_by('-added_date')[:15]

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
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    loan_date = models.DateField(default=timezone.now() + timedelta(days=calculate_next_saturday()))
    return_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(default=timezone.now() + timedelta(days=14))

    def __str__(self):
        return f"{self.item.title} loaned to {self.member.user.username}"

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