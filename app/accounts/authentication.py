from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from .redis_service import is_access_token_whitelisted

class RedisJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        validated = super().authenticate(request)

        if validated is None:
            return None

        user, token = validated
        token_str = request.headers.get("Authorization", "").split(" ")[1]

        if not is_access_token_whitelisted(token_str):
            raise exceptions.AuthenticationFailed("Token not whitelisted")

        return user, token
