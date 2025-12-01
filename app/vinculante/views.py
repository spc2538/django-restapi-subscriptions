from rest_framework import generics, permissions, status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import AccountUpdateSerializer, ForgotPasswordSerializer, MyTokenRefreshSerializer, RegisterSerializer, AccountSerializer, MyTokenObtainPairSerializer, ResetPasswordSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from .redis_service import redis_client, ACCESS_TOKEN_PREFIX, remove_all_user_tokens
from .redis_service import get_user_id_from_token, ACCESS_TOKEN_PREFIX, redis_client

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class MyTokenRefreshView(TokenRefreshView):
    serializer_class = MyTokenRefreshSerializer


class MeView(generics.RetrieveAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return Response({"detail": "Invalid authorization header"}, status=400)

        token_str = auth.split(" ")[1]
        user_id = get_user_id_from_token(token_str)

        if user_id is None:
            return Response({"detail": "Invalid token"}, status=400)

        remove_all_user_tokens(user_id)

        return Response({"detail": "Successfully logged out."})



class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    @swagger_auto_schema(request_body=ForgotPasswordSerializer)
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "Password reset code sent to email"})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    @swagger_auto_schema(request_body=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "Password has been reset successfully"})
    
class UpdateAccountView(generics.UpdateAPIView):
    serializer_class = AccountUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
