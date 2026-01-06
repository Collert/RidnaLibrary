from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('collection/item/<int:item_id>/', views.item, name='item'),
    path('collection/item/<int:item_id>/favourite/', views.favourite_item, name='favourite_item'),
    path('collection/item/<int:item_id>/borrow/', views.borrow_item, name='borrow_item'),
    path('collection/item/<int:item_id>/place_hold/', views.place_hold, name='place_hold'),
    path('collection/', views.collection, name='collection'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/all/', views.dashboard_all, name='dashboard_all'),
    path('dashboard/due_soon/', views.dashboard_due_soon, name='dashboard_due_soon'),
    path('dashboard/overdue/', views.dashboard_overdue, name='dashboard_overdue'),
    path('dashboard/history/', views.dashboard_history, name='dashboard_history'),
    path('favourites/', views.favourites, name='favourites'),
    path('events/', views.events, name='events'),
    path('events/<int:event_id>/', views.event, name='event'),
]