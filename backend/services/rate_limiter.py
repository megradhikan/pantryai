from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_id_or_ip(request) -> str:
    """
    Rate limit key: user UUID from verified JWT.
    Falls back to IP address if token is absent or invalid.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from services.auth import get_current_user
            return get_current_user(auth)
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_id_or_ip)
