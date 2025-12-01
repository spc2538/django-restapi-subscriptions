import stripe
from datetime import timedelta
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import generics, status
from drf_yasg.utils import swagger_auto_schema
from .serializers import CreateCheckoutSerializer
from subscriptions.models import SubscriptionType, UserSubscription
from django.utils import timezone
from django.contrib.auth import get_user_model

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateStripeCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=CreateCheckoutSerializer)
    def post(self, request):
        serializer = CreateCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_type = serializer.validated_data["subscription_type"]
        
        now = timezone.now()

        future_sub_exists = UserSubscription.objects.filter(
            user=user,
            is_active=False,
            start_date__gt=now
        ).exists()

        if future_sub_exists:
            return Response(
                {"error": "You already have a scheduled subscription change. Wait until it activates before making another purchase."},
                status=400
            )

        current = (
            UserSubscription.objects.filter(user=user, is_active=True)
            .order_by("-start_date")
            .first()
        )

        remaining_value = 0
        if current:
            remaining_days = (current.end_date - now).days
            if remaining_days > 0:
                daily_price = current.subscription_type.monthly_price / 30
                remaining_value = daily_price * remaining_days

        discount = remaining_value if current and new_type.monthly_price >= current.subscription_type.monthly_price else 0

        final_price = max(float(new_type.monthly_price) - float(discount), 0)

        amount_cents = int(final_price * 100)

        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=settings.FRONTEND_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_CANCEL_URL,
            customer_email=user.email,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "mxn",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": f"{new_type.name} Subscription",
                        },
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "user_id": user.id,
                "subscription_type_id": new_type.id,
            },
        )

        return Response({"checkout_url": session.url, "session_id": session.id})


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            user_id = session["metadata"]["user_id"]
            type_id = session["metadata"]["subscription_type_id"]

            User = get_user_model()

            user = User.objects.get(id=user_id)
            sub_type = SubscriptionType.objects.get(id=type_id)

            now = timezone.now()

            current = (
                UserSubscription.objects.filter(user=user, is_active=True)
                .order_by("-start_date")
                .first()
            )

            if not current:
                UserSubscription.objects.create(
                    user=user,
                    subscription_type=sub_type,
                    start_date=now,
                    end_date=now + timedelta(days=30),
                    is_active=True,
                    stripe_session_id=session["id"],
                    stripe_payment_intent=session["payment_intent"],
                )
            else:
                if sub_type.monthly_price > current.subscription_type.monthly_price:
                    current.is_active = False
                    current.save()

                    UserSubscription.objects.create(
                        user=user,
                        subscription_type=sub_type,
                        start_date=now,
                        end_date=now + timedelta(days=30),
                        is_active=True,
                        stripe_session_id=session["id"],
                        stripe_payment_intent=session["payment_intent"],
                    )
                else:
                    start = current.end_date
                    UserSubscription.objects.create(
                        user=user,
                        subscription_type=sub_type,
                        start_date=start,
                        end_date=start + timedelta(days=30),
                        is_active=False,
                        stripe_session_id=session["id"],
                        stripe_payment_intent=session["payment_intent"],
                    )

        return Response({"status": "success"})
