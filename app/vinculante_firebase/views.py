from rest_framework.views import APIView
from vinculante.redis_service import whitelist_access_token, whitelist_refresh_token
from django.conf import settings
from rest_framework.response import Response
from firebase_admin import auth as firebase_auth
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

class FirebaseLoginView(APIView):
    permission_classes = []

    def post(self, request):
        id_token = request.data.get("idToken")
        if not id_token:
            return Response({"error": "Missing Firebase ID token"}, status=400)

        try:
            decoded = firebase_auth.verify_id_token(id_token, clock_skew_seconds=60)
        except Exception as e:
            print(e)
            return Response({"error": "Invalid Firebase token"}, status=401)

        email = decoded.get("email")
        first_name = decoded.get("name") or ""

        User = get_user_model()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "first_name": first_name},
        )

        if created:
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        refresh_lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]

        whitelist_access_token(str(access), int(access_lifetime.total_seconds()))
        whitelist_refresh_token(str(refresh), int(refresh_lifetime.total_seconds()))

        return Response({
            "created": created,
            "access": str(access),
            "refresh": str(refresh),
        })
