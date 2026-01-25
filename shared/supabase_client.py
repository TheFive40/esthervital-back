import os
import requests
from typing import Optional, Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")


class SupabaseAdminError(Exception):
    pass


def create_user(email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a user in Supabase Auth using the service role key.

    Returns the created user object (as dict) on success. Raises SupabaseAdminError on failure.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
        raise SupabaseAdminError("Supabase admin credentials not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE)")

    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
        "Content-Type": "application/json",
    }

    payload = {"email": email, "password": password, "email_confirm": True}
    if user_metadata:
        payload["user_metadata"] = user_metadata

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        raise SupabaseAdminError(f"HTTP error creating Supabase user: {e}")

    if resp.status_code >= 400:
        # Try to include Supabase error message
        try:
            msg = resp.json()
        except Exception:
            msg = resp.text
        raise SupabaseAdminError(f"Supabase error ({resp.status_code}): {msg}")

    try:
        return resp.json()
    except Exception:
        raise SupabaseAdminError("Invalid JSON response from Supabase when creating user")


def delete_user(user_id: str) -> None:
    """Delete a Supabase Auth user by id (server-side). Raises SupabaseAdminError on failure."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
        raise SupabaseAdminError("Supabase admin credentials not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE)")

    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
    }

    try:
        resp = requests.delete(url, headers=headers, timeout=10)
    except Exception as e:
        raise SupabaseAdminError(f"HTTP error deleting Supabase user: {e}")

    if resp.status_code >= 400:
        try:
            msg = resp.json()
        except Exception:
            msg = resp.text
        raise SupabaseAdminError(f"Supabase error deleting user ({resp.status_code}): {msg}")

    return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user from Supabase Auth by email (scan list)."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
        return None

    # TODO: Pagination if many users. For now default page size usually covers dev usage.
    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/admin/users"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            users = data.get("users", [])
            for u in users:
                if u.get("email", "").lower() == email.lower():
                    return u
    except Exception:
        pass
    
    return None


def update_user_password(user_id: str, new_password: str) -> None:
    """Update a user's password in Supabase Auth."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
         raise SupabaseAdminError("Supabase admin credentials not configured")

    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/{user_id}"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
        "Content-Type": "application/json",
    }
    
    payload = {"password": new_password}
    
    try:
        resp = requests.put(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        raise SupabaseAdminError(f"HTTP error updating Supabase user: {e}")

    if resp.status_code >= 400:
        raise SupabaseAdminError(f"Supabase error updating user ({resp.status_code}): {resp.text}")
