import redis
from django.conf import settings
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken

redis_client = redis.StrictRedis.from_url(
    settings.CACHES["default"]["LOCATION"], decode_responses=True
)

ACCESS_TOKEN_PREFIX = "access_whitelist:user:{user_id}:"
REFRESH_TOKEN_PREFIX = "refresh_whitelist:user:{user_id}:"

def get_user_id_from_token(token: str):
    try:
        payload = UntypedToken(token)
        return payload.get("user_id")
    except InvalidToken:
        return None


def whitelist_access_token(token: str, lifetime_seconds: int):
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return

    key = ACCESS_TOKEN_PREFIX.format(user_id=user_id) + token
    redis_client.setex(key, lifetime_seconds, "1")


def is_access_token_whitelisted(token: str) -> bool:
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return False

    key = ACCESS_TOKEN_PREFIX.format(user_id=user_id) + token
    return redis_client.exists(key) == 1


def remove_access_token(token: str):
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return

    key = ACCESS_TOKEN_PREFIX.format(user_id=user_id) + token
    redis_client.delete(key)


def whitelist_refresh_token(token: str, lifetime_seconds: int):
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return

    key = REFRESH_TOKEN_PREFIX.format(user_id=user_id) + token
    redis_client.setex(key, lifetime_seconds, "1")


def is_refresh_token_whitelisted(token: str) -> bool:
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return False

    key = REFRESH_TOKEN_PREFIX.format(user_id=user_id) + token
    return redis_client.exists(key) == 1


def remove_refresh_token(token: str):
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return

    key = REFRESH_TOKEN_PREFIX.format(user_id=user_id) + token
    redis_client.delete(key)

def remove_all_user_tokens(user_id: int):
    patterns = [
        ACCESS_TOKEN_PREFIX.format(user_id=user_id) + "*",
        REFRESH_TOKEN_PREFIX.format(user_id=user_id) + "*",
    ]

    for pattern in patterns:
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break

