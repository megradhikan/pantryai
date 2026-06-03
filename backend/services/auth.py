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


def get_current_user(authorization: str = Header(...)) -> str:
    """
    Verifies Supabase-issued JWT from Authorization: Bearer <token> header.
    Returns user_id (UUID string) on success.
    Raises HTTP 401 on any failure.
    """
    try:
        token = authorization.removeprefix("Bearer ").strip()
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
