import os
import random
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from .models import FeaturedItem, HeroSection, Item, ItemHold, Loan, Book
from .enums import *
from django.core.paginator import Paginator
from django.db.models import Q
from urllib.parse import quote

def home(request):
    hero_section = HeroSection.objects.first()
    new_arrivals_all = Item.new_arrivals()
    new_arrivals = [new_arrivals_all[:5], new_arrivals_all[5:10], new_arrivals_all[10:15]]
    featured_item = random.choice(FeaturedItem.objects.all()) if FeaturedItem.objects.exists() else None
    return render(request, 'base/home.html', {
        'hero_section': hero_section, 
        'new_arrivals': new_arrivals, 
        'featured_item': featured_item
    })

def item(request, item_id):
    item = Book.objects.get(id=item_id)
    available_copies = item.available_copies()
    favourited_by_user = item.favourited_by.filter(id=request.user.id).exists()
    return render(request, 'base/item.html', {
        'item': item, 
        'available_copies': available_copies,
        'borrowed_by_user': item.is_borrowed_by(request.user) if request.user.is_authenticated else False,
        'requested_by_user': item.is_borrowed_and_not_received_by(request.user) if request.user.is_authenticated else False,
        'favourited_by_user': favourited_by_user,
        'on_hold_by_user': ItemHold.objects.filter(item=item, user=request.user).exists() if request.user.is_authenticated else False,
        'user_loan': Loan.objects.filter(item=item, user=request.user, return_date__isnull=True).first() if request.user.is_authenticated else None,
        'user_position_in_hold_queue': item.users_position_in_hold_queue(request.user) if request.user.is_authenticated else None,
    })

def borrow_item(request, item_id):
    if request.method == 'POST':
        item = Item.objects.get(id=item_id)
        
        cancel_request = request.POST.get('cancel-request')
        
        if cancel_request == 'true':
            existing_loan = Loan.objects.filter(item=item, user=request.user, received=False).first()
            if existing_loan:
                existing_loan.delete()
                messages.success(request, _("Item request cancelled successfully!"))
            else:
                messages.error(request, _("No pending request found to cancel."))
        elif cancel_request == 'false':
            if not item.is_available():
                messages.error(request, _("This item is currently not available for borrowing."))
            elif not request.user.is_authenticated:
                messages.error(request, _("You must be logged in to borrow items."))
            elif item.is_borrowed_by(request.user):
                messages.error(request, _("You have already borrowed this item and not yet returned it."))
            elif item.is_borrowed_and_not_received_by(request.user):
                messages.error(request, _("You have already requested this item and it is not yet received."))
            else:
                # Create a new loan
                loan = Loan.objects.create(item=item, user=request.user)
                messages.success(request, _("Item successfully borrowed! Pick it up on %(loan_date)s.") % {'loan_date': loan.loan_date})
        
        return redirect('item', item_id=item.id)
    else:
        return HttpResponseNotAllowed(['POST'])
    
def place_hold(request, item_id):
    if request.method == 'POST':
        item = Item.objects.get(id=item_id)
        response_messages = []
        if not request.user.is_authenticated:
            response_messages.append({'text': _("You must be logged in to place a hold."), 'level': 'error'})
        else:
            # Check if user already has a hold
            existing_hold = ItemHold.objects.filter(item=item, user=request.user).first()
            if existing_hold:
                response_messages.append({'text': _("You already have a hold on this item."), 'level': 'info'})
            else:
                ItemHold.objects.create(item=item, user=request.user)
                position = item.users_position_in_hold_queue(request.user)
                response_messages.append({'text': _("You have successfully placed a hold on this item. Your position in the queue is %(position)s.") % {'position': position}, 'level': 'success'})
        return JsonResponse({
            'messages': response_messages,
            "position_in_queue": position if 'position' in locals() else None
        })
    elif request.method == 'DELETE':
        item = Item.objects.get(id=item_id)
        response_messages = []
        if not request.user.is_authenticated:
            response_messages.append({'text': _("You must be logged in to cancel a hold."), 'level': 'error'})
        else:
            existing_hold = ItemHold.objects.filter(item=item, user=request.user).first()
            if existing_hold:
                existing_hold.delete()
                response_messages.append({'text': _("Your hold has been successfully cancelled."), 'level': 'success'})
            else:
                response_messages.append({'text': _("You do not have a hold on this item."), 'level': 'info'})
        return JsonResponse({
            'messages': response_messages
        })
    else:
        return HttpResponseNotAllowed(['POST', 'DELETE'])

def favourite_item(request, item_id):
    if request.method == 'POST':
        item = Item.objects.get(id=item_id)
        user = request.user
        if user.is_authenticated:
            if item.favourited_by.filter(id=user.id).exists():
                item.favourited_by.remove(user)
                favourited = False
            else:
                item.favourited_by.add(user)
                favourited = True
            return JsonResponse({'favourited': favourited})
        else:
            return JsonResponse({'error': _("User not authenticated")}, status=403)
    return HttpResponseNotAllowed(['POST'])

def collection(request):
    search = {
        "query": request.GET.get('search', ''),
        "genres": request.GET.getlist('genre'),
        "languages": request.GET.getlist('language'),
        "themes": request.GET.getlist('theme'),
        "tones": request.GET.getlist('tone'),
        "audiences": request.GET.getlist('audience'),
        "language_levels": request.GET.getlist('language_level'),
    }

    condition = Q()

    if search["query"]:
        condition &= (Q(title__icontains=search["query"]) |
                      Q(author__icontains=search["query"]) |
                      Q(description__icontains=search["query"]) |
                      Q(title_fr__icontains=search["query"]) |
                      Q(author_fr__icontains=search["query"]) |
                      Q(description_fr__icontains=search["query"]) |
                      Q(title_uk__icontains=search["query"]) |
                      Q(author_uk__icontains=search["query"]) |
                      Q(description_uk__icontains=search["query"]))
        
    if search["genres"]:
        condition &= Q(genre__in=search["genres"])

    if search["languages"]:
        condition &= Q(language__in=search["languages"])

    if search["themes"]:
        condition &= Q(theme__in=search["themes"])
    
    if search["tones"]:
        condition &= Q(tone__in=search["tones"])
    
    if search["audiences"]:
        condition &= Q(audience__in=search["audiences"])

    if search["language_levels"]:
        condition &= Q(language_level__in=search["language_levels"])

    items = Book.objects.filter(condition).order_by('-added_date')

    paginated_items = Paginator(items, 10)  # Show 10 items per page
    page_number = request.GET.get("page")
    page_obj = paginated_items.get_page(page_number)
    
    all_genres = Genre.choices_with_counts()
    all_languages = Language.choices_with_counts()
    all_themes = Theme.choices_with_counts()
    all_tones = Tone.choices_with_counts()
    all_audiences = Audience.choices_with_counts()
    all_language_levels = LanguageLevel.choices_with_counts()

    return render(request, 'base/collection.html', {
        'items': page_obj,
        'genres': [all_genres[:5], all_genres[5:]] if len(all_genres) > 5 else [all_genres],
        'languages': [all_languages[:5], all_languages[5:]] if len(all_languages) > 5 else [all_languages],
        'themes': [all_themes[:5], all_themes[5:]] if len(all_themes) > 5 else [all_themes],
        'tones': [all_tones[:5], all_tones[5:]] if len(all_tones) > 5 else [all_tones],
        'audiences': [all_audiences[:5], all_audiences[5:]] if len(all_audiences) > 5 else [all_audiences],
        'language_levels': [all_language_levels[:5], all_language_levels[5:]] if len(all_language_levels) > 5 else [all_language_levels],
        'search': search,
    })

def get_random_splash_screen():
    splash_screens = os.listdir('base/static/base/splash-screens/')
    filename = random.choice(splash_screens)
    # URL encode the filename to make it URL safe
    return quote(filename, safe='')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, _('Please fill in all fields.'))
            return render(request, 'base/login.html', {'bg_img': get_random_splash_screen()})
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.add_message(request, messages.INFO, _('Welcome back, %(username)s!') % {'username': user.username})
            # Redirect to the next page if specified, otherwise to home
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
        else:
            messages.error(request, _('Invalid username or password.'))
    
    return render(request, 'base/login.html', {'bg_img': get_random_splash_screen()})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, _('You have been successfully logged out.'))
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, _('Please fill in all fields.'))
            return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})
        
        if password1 != password2:
            messages.error(request, _('Passwords do not match.'))
            return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Username already exists. Please choose a different username.'))
            return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, _('Email already registered. Please use a different email or try logging in.'))
            return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})
        
        # Create a temporary user instance for password validation
        temp_user = User(username=username, email=email)
        
        try:
            # Validate password using Django's built-in validators
            validate_password(password1, temp_user)
        except ValidationError as e:
            # Django's password validation returns a list of errors
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})
        
        try:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            
            # Log the user in
            login(request, user)
            
            messages.success(request, _('Welcome to Ridna Library, %(username)s! Your account has been created successfully.') % {'username': user.username})
            return redirect('home')
        
        except Exception as e:
            messages.error(request, _('An error occurred while creating your account. Please try again.'))
            return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})
    
    return render(request, 'base/register.html', {'bg_img': get_random_splash_screen()})

def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_loans = Loan.objects.filter(user=request.user).order_by('-loan_date')
    user_holds = ItemHold.objects.filter(user=request.user).order_by('hold_date')
    favourite_items = Book.objects.filter(favourited_by=request.user)
    
    return render(request, 'base/profile.html', {
        'user_loans': user_loans,
        'user_holds': user_holds,
        'favourite_items': favourite_items,
    })