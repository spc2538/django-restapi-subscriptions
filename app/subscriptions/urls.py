from django.urls import path
from .views import (
    SubscriptionTypeListView,
    MySubscriptionView,
    PurchaseSubscriptionView,
    SubscriptionHistoryView
)

urlpatterns = [
    path("plans/", SubscriptionTypeListView.as_view(), name="subscription-types"),
    path("me/", MySubscriptionView.as_view(), name="my-subscription"),
#    path("purchase/", PurchaseSubscriptionView.as_view(), name="purchase-subscription"),
    path("history/", SubscriptionHistoryView.as_view(), name="subscription-history"),
]
