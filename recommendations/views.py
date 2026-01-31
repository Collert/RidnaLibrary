from django.shortcuts import render
from .models import Interaction, UserTagScore
from .enums import InteractionWeight
from base.models import Item
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
import json
from django.conf import settings

def record_interaction_api(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    body = json.loads(request.body)

    type = body.get('type')
    weight = InteractionWeight[type]
    item_id = body.get('item_id')

    item = Item.objects.get(id=item_id)
    scores = record_interaction(request.user, item, weight)
    return JsonResponse({"scores": scores}, safe=False)

def record_interaction(user, item: Item, weight: int):
    if not settings.DEBUG and Interaction.objects.filter(
        user=user, 
        item=item, 
        weight=weight, 
        timestamp__gte=timezone.now()-timezone.timedelta(minutes=15)
        ).exists():
        return []
    interaction = Interaction(user=user, weight=weight, item=item)
    interaction.save()

    tags = item.tags
    added_scores = []

    for tag in tags:
        ts_object, _ = UserTagScore.objects.get_or_create(tag=tag, user=user)
        ts_object.add_score(weight)
        added_scores.append({
            "tag": tag,
            "new_score": ts_object.score
        })
    return added_scores

def get_user_tag_scores(user):
    tag_scores = UserTagScore.objects.filter(user=user).order_by('-score')[:20]
    scores_list = {}
    for ts in tag_scores:
        scores_list[ts.tag] = ts.score
    return scores_list

def score_an_item_for_user(item: Item, user, multiplier=1.0, user_tag_scores=None):
    reasons = []
    tags = item.tags
    total_score = 0.0
    if user_tag_scores is None:
        user_tag_scores = get_user_tag_scores(user)
    for tag in tags:
        tag_score = user_tag_scores.get(tag, 0.0)
        if tag_score > 0:
            reasons.append((tag_score, tag))
        total_score += tag_score * multiplier
    reasons.sort(key=lambda x: x[0], reverse=True)
    return total_score, reasons[:3]