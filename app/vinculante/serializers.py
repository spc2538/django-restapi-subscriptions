import random
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from django.core.mail import send_mail

from .utils import generate_reset_token
from .redis_service import whitelist_access_token, whitelist_refresh_token
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'age', 'first_name', 'last_name']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'phone_number', 'age']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User._meta.get_field('email').name

    def validate(self, attrs):
        data = super().validate(attrs)

        access = data["access"]
        refresh = data["refresh"]

        access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        refresh_lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]

        whitelist_access_token(
            token=str(access),
            lifetime_seconds=int(access_lifetime.total_seconds())
        )

        whitelist_refresh_token(
            token=str(refresh),
            lifetime_seconds=int(refresh_lifetime.total_seconds())
        )

        return data
    
class MyTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        new_access = data["access"]
        access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]

        whitelist_access_token(
            token=str(new_access),
            lifetime_seconds=int(access_lifetime.total_seconds())
        )

        return data
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        token = generate_reset_token(user)

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        send_mail(
            subject="Password Reset",
            message=f"Click the link to reset your password:\n\n{reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return True


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        token_str = attrs["token"]

        try:
            token = AccessToken(token_str)
        except Exception:
            raise serializers.ValidationError("Invalid or expired reset token")

        # Validate its type
        if token.get("type") != "password_reset":
            raise serializers.ValidationError("Invalid token type")

        # Get user from token
        user_id = token.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User no longer exists")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return user
    
class AccountUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'age', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
