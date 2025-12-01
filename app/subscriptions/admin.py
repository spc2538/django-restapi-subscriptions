from django.contrib import admin
from .models import SubscriptionType, UserSubscription


@admin.register(SubscriptionType)
class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "monthly_price", "storage_limit_gb", "has_premium_features")
    search_fields = ("name",)
    list_filter = ("has_premium_features",)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "subscription_type",
        "start_date",
        "end_date",
        "is_active",
        "created_at_utc",
        "updated_at_utc",
    )
    list_filter = ("is_active", "subscription_type")
    search_fields = ("user__email",)
    autocomplete_fields = ("user", "subscription_type")
