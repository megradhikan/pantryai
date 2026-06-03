import os
from supabase import create_client, Client

_client: Client | None = None


def get_admin_client() -> Client:
    """
    Returns a singleton Supabase client using the service role key.
    This key bypasses RLS — never expose it to the frontend.
    Singleton pattern avoids creating a new connection on every request.
    """
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        _client = create_client(url, key)
    return _client
