from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from recommendations.models import UserRecommendationExtras

class Command(BaseCommand):
    help = 'Creates UserRecommendationExtras for users that don\'t have one'

    def handle(self, *args, **options):
        users_without_extras = User.objects.filter(recommendation_extras__isnull=True)
        count = users_without_extras.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All users already have recommendation extras'))
            return
        
        for user in users_without_extras:
            UserRecommendationExtras.objects.create(user=user)
            self.stdout.write(f'Created recommendation extras for user: {user.username}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} UserRecommendationExtras records'))
