from django.db import models
from django.conf import settings
from django.utils import timezone


class SubscriptionType(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    storage_limit_gb = models.PositiveIntegerField()
    has_premium_features = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    @property
    def is_future(self):
        return self.start_date > timezone.now()

    @property
    def is_current(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_active

    @property
    def is_past(self):
        return self.end_date < timezone.now() or not self.is_active
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )
    subscription_type = models.ForeignKey(
        SubscriptionType,
        on_delete=models.CASCADE,
        related_name="user_subscriptions"
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=255, null=True, blank=True)
    created_at_utc = models.DateTimeField(default=timezone.now)
    updated_at_utc = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.subscription_type.name}"
