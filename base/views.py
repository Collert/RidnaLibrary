import random
from django.shortcuts import render
from .models import FeaturedItem, HeroSection, Item

def home(request):
    hero_section = HeroSection.objects.first()
    new_arrivals_all = Item.new_arrivals(Item)
    new_arrivals = [new_arrivals_all[:5], new_arrivals_all[5:10], new_arrivals_all[10:15]]
    featured_item = random.choice(FeaturedItem.objects.all()) if FeaturedItem.objects.exists() else None
    return render(request, 'base/home.html', {'hero_section': hero_section, 'new_arrivals': new_arrivals, 'featured_item': featured_item})