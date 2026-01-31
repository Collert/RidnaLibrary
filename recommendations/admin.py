from base.admin import admin_site as admin

from .models import Interaction, UserTagScore, UserRecommendationExtras

admin.register(Interaction)
admin.register(UserTagScore)