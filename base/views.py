import datetime
import json
import os
import random
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _, ngettext
from .models import FeaturedItem, HeroSection, Item, ItemHold, Loan, Book, Event, FeaturedEvent, EventKind
from .enums import *
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from recommendations.views import record_interaction
from recommendations.enums import InteractionWeight


NEWSLETTER_SUBSCRIPTION_URL = 'https://marketing.uahelp.ca/api/public/subscription'
NEWSLETTER_REQUEST_TIMEOUT_SECONDS = 10


def _decode_newsletter_response(raw_body):
    if not raw_body:
        return {}

    try:
        return json.loads(raw_body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}

def home(request):
    hero_section = HeroSection.objects.first()
    new_arrivals_all = Item.new_arrivals()
    new_arrivals = [new_arrivals_all[:5], new_arrivals_all[5:10], new_arrivals_all[10:15]]
    featured_item = random.choice(FeaturedItem.objects.all()) if FeaturedItem.objects.exists() else None
    upcoming_events = list(
        Event.objects.filter(event_date__gte=timezone.now()).order_by('event_date')[:3]
    )
    return render(request, 'base/home.html', {
        'hero_section': hero_section, 
        'new_arrivals': new_arrivals, 
        'featured_item': featured_item.item if featured_item else None,
        'upcoming_events': upcoming_events,
    })


def newsletter_subscribe(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    upstream_payload = urlencode({
        'email': request.POST.get('email', '').strip(),
        'l': request.POST.get('l', '').strip(),
    }).encode('utf-8')
    upstream_request = Request(
        NEWSLETTER_SUBSCRIPTION_URL,
        data=upstream_payload,
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )

    try:
        with urlopen(upstream_request, timeout=NEWSLETTER_REQUEST_TIMEOUT_SECONDS) as response:
            status_code = response.getcode()
            response_payload = _decode_newsletter_response(response.read())
    except HTTPError as exc:
        status_code = exc.code
        response_payload = _decode_newsletter_response(exc.read())
    except URLError:
        status_code = 502
        response_payload = {
            'message': _('We could not reach the newsletter service. Please try again.'),
        }

    response_payload.setdefault(
        'message',
        _('Thanks for subscribing!') if 200 <= status_code < 300 else _('Something went wrong. Please try again.'),
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response_payload, status=status_code)

    if 200 <= status_code < 300:
        messages.success(request, response_payload['message'])
    else:
        messages.error(request, response_payload['message'])

    return redirect(get_next_redirect_target(request, default_url_name='home'))

def item(request, item_id):
    item = Book.objects.get(pk=item_id)
    available_copies = item.available_copies()
    favourited_by_user = item.favourited_by.filter(id=request.user.id).exists()
    record_interaction(request.user, item, InteractionWeight.VIEW)
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
        record_interaction(request.user, item, InteractionWeight.BORROW)
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
        record_interaction(user, item, InteractionWeight.FAVOURITE)
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

def books(request):
    return collection(request, collection_type='book')

def film(request):
    return collection(request, collection_type='film')

def music(request):
    return collection(request, collection_type='music')

def sell(request):
    return collection(request, collection_type='sell')

def for_you(request):
    return collection(request, collection_type='personalized')

def collection(request, collection_type=None):
    # Log top picks in a readable format for debugging
    # if request.user.is_authenticated:
    #     top_picks = Item.get_top_picks_for_user(request.user)
    #     if top_picks:
    #         formatted_picks = []
    #         for idx, (item_obj, score, reasons) in enumerate(top_picks, start=1):
    #             reasons_text = ", ".join(f"{reason_score:.1f} {tag}" for reason_score, tag in reasons)
    #             formatted_picks.append(f"{idx}. {item_obj} — score {score:.1f} ({reasons_text})")
    #         print("Top picks for user:\n" + "\n".join(formatted_picks))
    #     else:
    #         print("Top picks for user: none")
    search = {
        "query": request.GET.get('search', ''),
        "genres": request.GET.getlist('genre'),
        "languages": request.GET.getlist('language'),
        "themes": request.GET.getlist('theme'),
        "tones": request.GET.getlist('tone'),
        "audiences": request.GET.getlist('audience'),
        "language_levels": request.GET.getlist('language_level'),
    }
    
    if not any(search.values()) and not collection_type:
        return redirect('for_you')

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

    if collection_type == 'book':
        items = Book.objects.filter(condition).order_by('-added_date')
    elif collection_type == 'personalized':
        if request.user.is_authenticated:
            items = Item.get_top_picks_for_user(request.user)
        else:
            items = Item.objects.all()

    paginated_items = Paginator(items, 10)  # Show 10 items per page
    page_number = request.GET.get("page")
    page_obj = paginated_items.get_page(page_number)
    
    all_genres = Genre.get_choices_with_counts()
    all_languages = Language.get_choices_with_counts()
    all_themes = Theme.get_choices_with_counts()
    all_tones = Tone.get_choices_with_counts()
    all_audiences = Audience.get_choices_with_counts()
    all_language_levels = LanguageLevel.get_choices_with_counts()

    return render(request, 'base/collection.html', {
        'items': page_obj,
        'genres': [all_genres[:5], all_genres[5:]] if len(all_genres) > 5 else [all_genres],
        'languages': [all_languages[:5], all_languages[5:]] if len(all_languages) > 5 else [all_languages],
        'themes': [all_themes[:5], all_themes[5:]] if len(all_themes) > 5 else [all_themes],
        'tones': [all_tones[:5], all_tones[5:]] if len(all_tones) > 5 else [all_tones],
        'audiences': [all_audiences[:5], all_audiences[5:]] if len(all_audiences) > 5 else [all_audiences],
        'language_levels': [all_language_levels[:5], all_language_levels[5:]] if len(all_language_levels) > 5 else [all_language_levels],
        'search': search,
        'collection_type': collection_type,
    })

def get_random_splash_screen():
    splash_screens = os.listdir('base/static/base/splash-screens/')
    filename = random.choice(splash_screens)
    # URL encode the filename to make it URL safe
    return quote(filename, safe='')


def get_next_redirect_target(request, default_url_name='dashboard'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse(default_url_name)

def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    context = {
        'bg_img': get_random_splash_screen(),
        'next': next_url,
    }

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, _('Please fill in all fields.'))
            return render(request, 'base/login.html', context)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.add_message(request, messages.INFO, _('Welcome back, %(username)s!') % {'username': user.username})
            overdue_count = Loan.objects.filter(user=user, return_date__isnull=True, due_date__lt=timezone.localdate()).count()
            if overdue_count:
                messages.warning(
                    request,
                    ngettext(
                        'You have %(count)s overdue item. Please return it as soon as possible.',
                        'You have %(count)s overdue items. Please return them as soon as possible.',
                        overdue_count,
                    )
                    % {'count': overdue_count},
                )
            return redirect(get_next_redirect_target(request))
        else:
            messages.error(request, _('Invalid username or password.'))
    
    return render(request, 'base/login.html', context)

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
    
    return redirect('dashboard')

@login_required
def dashboard(request, kind=''):
    counts = {
        'all': Loan.objects.filter(user=request.user, return_date__isnull=True).count(),
        'due_soon': Loan.objects.filter(user=request.user, due_date__lte=timezone.now() + timezone.timedelta(days=4), return_date__isnull=True).count(),
        'overdue': Loan.objects.filter(user=request.user, due_date__lt=timezone.now(), return_date__isnull=True).count(),
    }
    if kind == 'overdue':
        items = Loan.objects.filter(user=request.user, due_date__lt=timezone.now(), return_date__isnull=True).order_by('due_date')
        return render(request, 'base/dashboard.html', {
            'items': items, 
            'counts': counts
            })
    elif kind == 'due_soon':
        items = Loan.objects.filter(user=request.user, due_date__lte=timezone.now() + timezone.timedelta(days=4), return_date__isnull=True).order_by('due_date')
        return render(request, 'base/dashboard.html', {
            'items': items, 
            'counts': counts
            })
    elif kind == 'all':
        items = Loan.objects.filter(user=request.user, return_date__isnull=True).order_by('-loan_date')
        return render(request, 'base/dashboard.html', {
            'items': items, 
            'counts': counts
            })
    elif kind == 'history':
        items = Loan.objects.filter(user=request.user, return_date__isnull=False).order_by('-loan_date')
        return render(request, 'base/dashboard.html', {
            'items': items, 
            'counts': counts
            })
    return redirect('dashboard_all')

@login_required
def dashboard_all(request):
    return dashboard(request, kind='all')

@login_required
def dashboard_due_soon(request):
    return dashboard(request, kind='due_soon')

@login_required
def dashboard_overdue(request):
    return dashboard(request, kind='overdue')

@login_required
def dashboard_history(request):
    return dashboard(request, kind='history')

@login_required
def favourites(request):
    favourite_items = request.user.favourite_items.all().order_by('-added_date')
    
    return render(request, 'base/favourites.html', {
        'favourite_items': favourite_items
    })


def build_login_redirect_url(next_url):
    return f"{reverse('login')}?next={quote(next_url)}"

def events(request):
    search = {
        "days": request.GET.getlist('day'),
        "event_types": request.GET.getlist('event_type'),
    }

    condition = Q(event_date__gte=timezone.now())

    if search["days"]:
        day_conditions = Q()
        if 'wd' in search["days"]:
            day_conditions |= Q(event_date__week_day__in=[2,3,4,5,6])  # Monday to Friday
        if 'we' in search["days"]:
            day_conditions |= Q(event_date__week_day__in=[1,7])  # Saturday and Sunday
        condition &= day_conditions
    if search["event_types"]:
        condition &= Q(kind__in=search["event_types"])

    events = Event.objects.filter(condition).order_by('event_date')
    try:
        featured_event = random.choice(FeaturedEvent.objects.all())
    except IndexError:
        featured_event = None
    paginated_events = Paginator(events, 5)  # Show 5 events per page
    page_number = request.GET.get("page")
    page_obj = paginated_events.get_page(page_number)
    return render(request, 'base/events.html', {
        'page_obj': page_obj,
        'all_events': Event.objects.all(),
        'featured_event': featured_event.event if featured_event else None,
        'event_types': EventKind.get_choices_with_counts(),
        'search': search,
        "days_counts": Event.get_counts_by_weekday_weekend(),
        })

def event(request, event_id):
    event = Event.objects.get(pk=event_id)
    is_interested = event.interested_users.filter(id=request.user.id).exists() if request.user.is_authenticated else False
    return render(request, 'base/event.html', {
        'event': event,
        'is_interested': is_interested,
        'can_express_interest': request.user.is_authenticated,
        'interest_login_url': build_login_redirect_url(request.get_full_path()),
    })

def build_ical_response(*, summary, description, location, start_dt, end_dt, uid, filename):
    """Build an HttpResponse containing a minimal iCalendar file."""

    def fmt_dt(value):
        return value.astimezone(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    def escape(text):
        return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

    ical_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Ridna Library//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{fmt_dt(timezone.now())}\r\n"
        f"DTSTART:{fmt_dt(start_dt)}\r\n"
        f"DTEND:{fmt_dt(end_dt)}\r\n"
        f"SUMMARY:{escape(summary)}\r\n"
        f"DESCRIPTION:{escape(description)}\r\n"
        f"LOCATION:{escape(location)}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    response = HttpResponse(ical_content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def event_ical(request, event_id):
    """Generate a downloadable iCalendar invite for the event."""
    event = get_object_or_404(Event, pk=event_id)

    # Build the event time window; iCal needs explicit start/end in UTC
    start_dt = timezone.localtime(event.event_date)
    end_dt = start_dt + timezone.timedelta(hours=1)

    return build_ical_response(
        summary=event.get_localized_title(),
        description=event.get_localized_description(),
        location=event.address,
        start_dt=start_dt,
        end_dt=end_dt,
        uid=f"event-{event.id}@ridna-library",
        filename=f"ridna-library-event-{event.id}.ics",
    )

def toggle_event_interest(request, event_id):
    if request.method == 'POST':
        event = Event.objects.get(pk=event_id)
        user = request.user
        if user.is_authenticated:
            if event.interested_users.filter(id=user.id).exists():
                event.interested_users.remove(user)
                interested = False
            else:
                event.interested_users.add(user)
                interested = True
            return JsonResponse({'interested': interested})
        else:
            return JsonResponse({
                'error': _("User not authenticated"),
                'login_url': build_login_redirect_url(reverse('event', args=[event_id])),
            }, status=401)
    return HttpResponseNotAllowed(['POST'])

