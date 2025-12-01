from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import UserSubscription


@shared_task
def activate_scheduled_subscriptions():
    """
    1. Deactivate subscriptions whose end_date has already passed.
    2. Activate subscriptions whose start_date has arrived (UTC),
       only if the user has no other active subscription.
    """
    now = timezone.now()

    ended_qs = UserSubscription.objects.filter(
        end_date__lte=now,
        is_active=True
    )

    for ended in ended_qs.select_related('user'):
        ended.is_active = False
        ended.save()

    candidates = UserSubscription.objects.filter(
        start_date__lte=now,
        end_date__gt=now,
        is_active=False
    ).order_by("start_date")

    for candidate in candidates.select_related("user"):
        user = candidate.user

        with transaction.atomic():
            active_exists = (
                UserSubscription.objects
                .select_for_update()
                .filter(user=user, is_active=True)
                .exists()
            )

            if not active_exists:
                candidate.is_active = True
                candidate.save()
