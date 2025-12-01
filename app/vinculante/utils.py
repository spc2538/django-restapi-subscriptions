from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

def generate_reset_token(user):
    token = RefreshToken.for_user(user)
    token.set_exp(lifetime=timedelta(minutes=15))
    access_token = token.access_token

    access_token["type"] = "password_reset"

    return str(access_token)
