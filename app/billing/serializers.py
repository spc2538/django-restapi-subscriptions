from rest_framework import serializers
from subscriptions.models import SubscriptionType

class CreateCheckoutSerializer(serializers.Serializer):
    subscription_type_id = serializers.IntegerField()

    def validate(self, attrs):
        try:
            attrs["subscription_type"] = SubscriptionType.objects.get(
                id=attrs["subscription_type_id"]
            )
        except SubscriptionType.DoesNotExist:
            raise serializers.ValidationError("Invalid subscription type ID")

        return attrs
