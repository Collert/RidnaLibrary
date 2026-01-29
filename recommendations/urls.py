from django.urls import path
from . import views


urlpatterns = [
    path('record_interaction/', views.record_interaction_api, name='record_interaction'),
]