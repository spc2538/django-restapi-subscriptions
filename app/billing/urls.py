from django.urls import path
from .views import (
    CreateStripeCheckoutView,
    StripeWebhookView,
)

urlpatterns = [
    path("checkout/create/", CreateStripeCheckoutView.as_view()),
    path("stripe/webhook/", StripeWebhookView.as_view()),
]
