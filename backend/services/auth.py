import os
import json
import urllib.request
from fastapi import Header, HTTPException
import jwt as pyjwt
from jwt import PyJWKClient

_jwks_client = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        jwks_url = f"{url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def _verify(authorization: str) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    client = _get_jwks_client()
    signing_key = client.get_signing_key_from_jwt(token)
    return pyjwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256"],
        options={"verify_aud": False},
    )


def get_current_user(authorization: str = Header(...)) -> str:
    """
    Verifies Supabase-issued JWT from Authorization: Bearer <token> header.
    Returns user_id (UUID string) on success.
    Raises HTTP 401 on any failure.
    """
    try:
        payload = _verify(authorization)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return user_id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_admin(authorization: str = Header(...)) -> str:
    """
    Verifies the JWT and additionally requires the token's email to match
    ADMIN_EMAIL. Used for aggregate/cross-user endpoints that must not be
    reachable by ordinary authenticated users. Raises 401 if unauthenticated,
    403 if authenticated but not the admin.
    """
    try:
        payload = _verify(authorization)
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    admin_email = os.environ.get("ADMIN_EMAIL")
    if not admin_email or not email or email.lower() != admin_email.lower():
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id
