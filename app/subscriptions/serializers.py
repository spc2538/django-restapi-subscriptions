from rest_framework import serializers
from .models import SubscriptionType, UserSubscription


class SubscriptionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionType
        fields = "__all__"


class UserSubscriptionSerializer(serializers.ModelSerializer):
    subscription_type = SubscriptionTypeSerializer()

    class Meta:
        model = UserSubscription
        fields = "__all__"


class PurchaseSubscriptionSerializer(serializers.Serializer):
    subscription_type_id = serializers.IntegerField()

    def validate(self, attrs):
        from .models import SubscriptionType
        try:
            attrs["subscription_type"] = SubscriptionType.objects.get(
                id=attrs["subscription_type_id"]
            )
        except SubscriptionType.DoesNotExist:
            raise serializers.ValidationError("Invalid subscription type ID")
        return attrs

class UserSubscriptionHistorySerializer(serializers.ModelSerializer):
    subscription_type = SubscriptionTypeSerializer()

    class Meta:
        model = UserSubscription
        fields = "__all__"
