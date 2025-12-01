from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import generics, status

from .models import SubscriptionType, UserSubscription
from .serializers import (
    SubscriptionTypeSerializer,
    UserSubscriptionSerializer,
    PurchaseSubscriptionSerializer,
    UserSubscriptionHistorySerializer
)


class SubscriptionTypeListView(APIView):
    """
    Public endpoint — but if user is logged in,
    include proration/discount preview.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        types = SubscriptionType.objects.all()
        user = request.user

        if not user.is_authenticated:
            return Response(SubscriptionTypeSerializer(types, many=True).data)

        now = timezone.now()

        current = (
            UserSubscription.objects.filter(user=user, is_active=True)
            .order_by("-start_date")
            .first()
        )

        remaining_value = 0
        remaining_days = 0
        current_name = None

        if current and current.end_date > now:
            current_name = current.subscription_type.name

            remaining_days = (current.end_date - now).days
            if remaining_days > 0:
                daily_price = current.subscription_type.monthly_price / 30
                remaining_value = daily_price * remaining_days

        enhanced = []

        for t in types:
            discount = 0
            final_price = t.monthly_price

            if current and t.id != current.subscription_type.id:
                
                if t.monthly_price >= current.subscription_type.monthly_price:
                    discount = remaining_value
                    final_price = max(t.monthly_price - remaining_value, 0)

            enhanced.append({
                "id": t.id,
                "name": t.name,
                "monthly_price": t.monthly_price,
                "storage_limit_gb": t.storage_limit_gb,
                "has_premium_features": t.has_premium_features,
                "discount": round(discount, 2),
                "final_price": round(final_price, 2),
            })


        return Response({
            "current_subscription": current_name,
            "remaining_days": remaining_days,
            "remaining_value": round(remaining_value, 2),
            "subscription_types": enhanced
        })



class MySubscriptionView(APIView):
    """Logged-in user subscription status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = (
            UserSubscription.objects.filter(user=request.user, is_active=True)
            .order_by("-start_date")
            .first()
        )

        if not subscription:
            return Response({"detail": "No active subscription."})

        return Response(UserSubscriptionSerializer(subscription).data)


class PurchaseSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PurchaseSubscriptionSerializer

    @swagger_auto_schema(request_body=PurchaseSubscriptionSerializer)
    def post(self, request):
        serializer = PurchaseSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_type = serializer.validated_data["subscription_type"]
        user = request.user
        now = timezone.now()

        current = (
            UserSubscription.objects.filter(user=user, is_active=True)
            .order_by("-start_date")
            .first()
        )

        future = (
            UserSubscription.objects.filter(user=user, start_date__gt=now)
            .order_by("start_date")
            .first()
        )

        if not current:
            new_sub = UserSubscription.objects.create(
                user=user,
                subscription_type=new_type,
                start_date=now,
                end_date=now + timedelta(days=30),
                is_active=True,
            )
            return Response(UserSubscriptionSerializer(new_sub).data, status=201)

        if future:
            if (
                new_type.monthly_price > current.subscription_type.monthly_price and
                future.subscription_type.id == current.subscription_type.id
            ):
                pass
            else:
                return Response(
                    {"detail": "You already have an active and a future subscription. Cannot buy another."},
                    status=400
                )

        if current.subscription_type.id == new_type.id:
            start = current.end_date
            end = start + timedelta(days=30)

            new_sub = UserSubscription.objects.create(
                user=user,
                subscription_type=new_type,
                start_date=start,
                end_date=end,
                is_active=False,
            )

            return Response({
                "detail": "Subscription added to queue (same type).",
                "subscription": UserSubscriptionSerializer(new_sub).data
            }, status=201)

        is_upgrade = new_type.monthly_price > current.subscription_type.monthly_price
        is_downgrade = new_type.monthly_price < current.subscription_type.monthly_price

        if is_downgrade:
            start = current.end_date
            end = start + timedelta(days=30)

            new_sub = UserSubscription.objects.create(
                user=user,
                subscription_type=new_type,
                start_date=start,
                end_date=end,
                is_active=False
            )

            return Response({
                "detail": "Downgrade queued. Will activate after current plan ends.",
                "subscription": UserSubscriptionSerializer(new_sub).data
            }, status=201)

        if future and is_upgrade:
            basic_price = current.subscription_type.monthly_price

            full_remaining_days = (future.end_date - now).days
            daily_basic = basic_price / 30

            full_remaining_value = full_remaining_days * daily_basic
            final_price = new_type.monthly_price + full_remaining_value

            current.is_active = False
            current.save()
            future.delete()

            new_sub = UserSubscription.objects.create(
                user=user,
                subscription_type=new_type,
                start_date=now,
                end_date=now + timedelta(days=30),
                is_active=True,
            )

            return Response({
                "detail": "Upgraded across both queued periods.",
                "full_gap_charge": round(full_remaining_value, 2),
                "final_price": round(final_price, 2),
                "subscription": UserSubscriptionSerializer(new_sub).data
            }, status=201)

        current.is_active = False
        current.save()

        remaining_days = (current.end_date - now).days
        remaining_value = 0
        if remaining_days > 0:
            daily_price = current.subscription_type.monthly_price / 30
            remaining_value = float(daily_price * remaining_days)

        final_price = max(float(new_type.monthly_price) - remaining_value, 0)

        new_sub = UserSubscription.objects.create(
            user=user,
            subscription_type=new_type,
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
        )

        return Response({
            "detail": "Upgraded successfully.",
            "discount_applied": round(remaining_value, 2),
            "final_price": round(final_price, 2),
            "subscription": UserSubscriptionSerializer(new_sub).data
        }, status=201)

class SubscriptionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        subs = UserSubscription.objects.filter(user=user).order_by("-start_date")

        active = []
        past = []
        future = []

        for s in subs:
            if s.start_date <= now <= s.end_date and s.is_active:
                active.append(s)
            elif s.start_date > now:
                future.append(s)
            else:
                past.append(s)

        return Response({
            "active": UserSubscriptionHistorySerializer(active, many=True).data,
            "past": UserSubscriptionHistorySerializer(past, many=True).data,
            "future": UserSubscriptionHistorySerializer(future, many=True).data,
        })
