from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from .enums import InteractionWeight

class UserTagScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=100)
    score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('user', 'tag')

    def decayed_score(self):
        extras, _ = UserRecommendationExtras.objects.get_or_create(user=self.user)
        return self.score * 0.5**((timezone.now() - extras.last_recommendation_update).days / 60)
    
    def add_score(self, number):
        self.score = self.decayed_score()
        extras, _ = UserRecommendationExtras.objects.get_or_create(user=self.user)
        extras.last_recommendation_update = timezone.now()
        extras.save()
        self.score += number
        self.save()
        return self.score

    def __str__(self):
        return f"{self.user.username} - {self.tag}: {self.score}"
    
class Interaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight = models.PositiveSmallIntegerField(choices=InteractionWeight.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    item = models.ForeignKey('base.Item', on_delete=models.CASCADE, null=True)

class UserRecommendationExtras(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendation_extras')
    last_recommendation_update = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=User)
def create_user_recommendation_extras(sender, instance, created, **kwargs):
    if created:
        UserRecommendationExtras.objects.create(user=instance)

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.lower().replace(' ', '-')
        super().save(*args, **kwargs)