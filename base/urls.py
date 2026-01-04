from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('collection/books/<int:item_id>/', views.books, name='books_item'),
    path('collection/item/<int:item_id>/favourite/', views.favourite_item, name='favourite_item'),
    path('collection/item/<int:item_id>/borrow/', views.borrow_item, name='borrow_item'),
    path('collection/item/<int:item_id>/place_hold/', views.place_hold, name='place_hold'),
    path('collection/', views.collection, name='collection'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
]