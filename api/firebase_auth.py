import os
import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from django.http import JsonResponse
from functools import wraps

_initialized = False


def _init_firebase():
    global _initialized
    if _initialized:
        return

    # Configure emulator for local development
    emulator_host = getattr(settings, "FIREBASE_AUTH_EMULATOR_HOST", None)
    if emulator_host:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = emulator_host

    cred_path = getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", None)
    if cred_path:
        cred = credentials.Certificate(cred_path)
    else:
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred, {"projectId": settings.FIRESTORE_PROJECT_ID})
    _initialized = True


def verify_token(id_token: str) -> dict | None:
    """Verify Firebase ID token, return decoded claims or None."""
    _init_firebase()
    try:
        return auth.verify_id_token(id_token)
    except Exception:
        return None


def firebase_login_required(view_func):
    """Decorator requiring valid Firebase token."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authorization required"}, status=401)

        token = auth_header[7:]  # Strip 'Bearer '
        user = verify_token(token)

        if not user:
            return JsonResponse({"error": "Invalid token"}, status=401)

        request.firebase_user = user
        return view_func(request, *args, **kwargs)

    return wrapper
