from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('collection/item/<int:item_id>/', views.item, name='item'),
    path('collection/item/<int:item_id>/favourite/', views.favourite_item, name='favourite_item'),
    path('collection/item/<int:item_id>/borrow/', views.borrow_item, name='borrow_item'),
    path('collection/item/<int:item_id>/place_hold/', views.place_hold, name='place_hold'),
]