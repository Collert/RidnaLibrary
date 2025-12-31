import random
from django.contrib import messages
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from .models import FeaturedItem, HeroSection, Item, ItemHold
from .models import Loan

def home(request):
    hero_section = HeroSection.objects.first()
    new_arrivals_all = Item.new_arrivals(Item)
    new_arrivals = [new_arrivals_all[:5], new_arrivals_all[5:10], new_arrivals_all[10:15]]
    featured_item = random.choice(FeaturedItem.objects.all()) if FeaturedItem.objects.exists() else None
    return render(request, 'base/home.html', {
        'hero_section': hero_section, 
        'new_arrivals': new_arrivals, 
        'featured_item': featured_item
    })

def item(request, item_id):
    item = Item.objects.get(id=item_id)
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