from django.db import models

class InteractionWeight(models.IntegerChoices):
    VIEW = 1, 'View'
    LINGER = 2, 'Linger'
    VIEW_DESCRIPTION = 3, 'View Description'
    FAVOURITE = 5, 'Favourite'
    BORROW = 7, 'Borrow'